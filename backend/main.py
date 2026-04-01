"""
虚拟主播后端服务
- 接收弹幕
- AI对话处理（使用智能体）
- TTS语音合成
- WebSocket实时通信
"""

import json
import random
import time
import asyncio
import traceback
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory

# 导入智能体
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from agent import get_agent

app = Flask(__name__, static_folder='../', static_url_path='')

# 配置路径
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
AUDIO_DIR = BASE_DIR / "assets" / "audio"

# 确保目录存在
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# 加载配置
with open(CONFIG_DIR / "settings.json", "r", encoding="utf-8") as f:
    settings = json.load(f)

with open(CONFIG_DIR / "persona.md", "r", encoding="utf-8") as f:
    persona = f.read()


class VirtualLiver:
    """虚拟主播核心类"""

    def __init__(self):
        self.viewers = set()
        self.last_greeting_time = time.time()
        self.is_live = False
        self.tts_available = True
        # 初始化智能体
        self.agent = get_agent()

    async def generate_tts(self, text: str) -> str:
        """将文字转为语音"""
        if not self.tts_available:
            return None

        try:
            import edge_tts
            timestamp = int(time.time() * 1000)
            filename = f"response_{timestamp}.mp3"
            filepath = AUDIO_DIR / filename

            communicate = edge_tts.Communicate(
                text,
                voice=settings["voice"],
                rate=settings["rate"],
                pitch=settings["pitch"]
            )
            await communicate.save(str(filepath))

            return str(filepath)
        except Exception as e:
            print(f"⚠️ TTS 生成失败: {e}")
            self.tts_available = False
            return None

    def generate_response(self, danmu: str, username: str) -> str:
        """使用智能体生成回复"""
        try:
            return self.agent.generate_response(username, danmu)
        except Exception as e:
            print(f"⚠️ 智能体生成回复失败: {e}")
            # 回退到简单回复
            return f"@{username} 说得对！"
    
    async def process_danmu_async(self, danmu_data: dict) -> dict:
        """处理弹幕（异步）"""
        user_id = danmu_data.get("user_id", "unknown")
        content = danmu_data.get("content", "")
        username = danmu_data.get("username", "观众")
        
        response = self.generate_response(content, username)
        audio_path = await self.generate_tts(response)
        
        return {
            "text": response,
            "audio": audio_path,
            "user": username
        }
    
    async def welcome_async(self, username: str) -> dict:
        """欢迎新观众（异步）"""
        response = f"欢迎 @{username} 进入直播间~点点关注不迷路哦~"
        audio_path = await self.generate_tts(response)
        return {"text": response, "audio": audio_path, "user": username}


# 全局实例
liver = VirtualLiver()


def run_async(coro):
    """运行异步函数"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Flask API
@app.route("/api/danmu", methods=["POST"])
def receive_danmu():
    """接收弹幕"""
    try:
        data = request.json
        result = run_async(liver.process_danmu_async(data))
        return jsonify({"success": True, "data": result})
    except Exception as e:
        print(f"❌ 处理弹幕失败: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "error": str(e),
            "data": {
                "text": liver.generate_response(
                    data.get("content", "") if data else "",
                    data.get("username", "观众") if data else "观众"
                ),
                "audio": None,
                "user": data.get("username", "观众") if data else "观众"
            }
        }), 200


@app.route("/api/welcome", methods=["POST"])
def welcome():
    """欢迎观众"""
    try:
        data = request.json
        username = data.get("username", "新朋友") if data else "新朋友"
        result = run_async(liver.welcome_async(username))
        return jsonify({"success": True, "data": result})
    except Exception as e:
        print(f"❌ 欢迎失败: {e}")
        return jsonify({
            "success": True,
            "data": {
                "text": f"欢迎 @{data.get('username', '新朋友')} 进入直播间~",
                "audio": None,
                "user": data.get("username", "新朋友") if data else "新朋友"
            }
        }), 200


@app.route("/api/tts", methods=["POST"])
def tts():
    """文字转语音"""
    try:
        data = request.json
        text = data.get("text", "")
        if not text:
            return jsonify({"success": False, "error": "文字不能为空"})
        
        result = run_async(liver.generate_tts(text))
        return jsonify({"success": True, "audio": result})
    except Exception as e:
        print(f"❌ TTS 失败: {e}")
        return jsonify({"success": False, "error": str(e), "audio": None})


@app.route("/api/status", methods=["GET"])
def status():
    """状态查询"""
    return jsonify({
        "status": "running",
        "is_live": liver.is_live,
        "name": settings["name"],
        "tts_available": liver.tts_available
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/reset", methods=["POST"])
def reset_memory():
    """重置智能体记忆"""
    liver.agent.memory.clear()
    return jsonify({"success": True, "message": "记忆已重置"})


@app.route("/api/history", methods=["GET"])
def get_history():
    """获取对话历史"""
    context = liver.agent.memory.get_context()
    return jsonify({"success": True, "history": context})


@app.route("/", methods=["GET"])
def index():
    """前端界面"""
    return send_from_directory(BASE_DIR, "frontend.html")


@app.route("/assets/audio/<path:filename>", methods=["GET"])
def serve_audio(filename):
    """提供音频文件"""
    return send_from_directory(AUDIO_DIR, filename)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    print(f"🤖 虚拟主播 [{settings['name']}] 服务启动中...")
    print(f"📁 音频输出目录: {AUDIO_DIR}")
    print(f"🔊 使用语音: {settings['voice']}")
    print("\nAPI接口:")
    print("  POST /api/danmu   - 接收弹幕，返回AI回复")
    print("  POST /api/welcome - 欢迎观众")
    print("  POST /api/tts     - 文字转语音")
    print("  GET  /api/status  - 查看状态")
    
    app.run(host="0.0.0.0", port=port, debug=False)
