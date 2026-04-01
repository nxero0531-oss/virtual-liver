"""
虚拟主播后端服务
- 接收弹幕
- AI对话处理
- TTS语音合成
- WebSocket实时通信
"""

import json
import random
import time
import asyncio
from pathlib import Path

import edge_tts
from flask import Flask, request, jsonify

app = Flask(__name__)

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
        
    async def generate_tts(self, text: str) -> str:
        """将文字转为语音"""
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
    
    def generate_response(self, danmu: str, username: str) -> str:
        """生成回复"""
        danmu_lower = danmu.lower().strip()
        
        # 打招呼
        if any(k in danmu_lower for k in ["你好", "hello", "hi", "大家好"]):
            return f"你好呀~@{username}！欢迎来看小悠直播~"
        
        # 问名字
        if "名字" in danmu or "叫什么" in danmu:
            return f"我叫{settings['name']}呀~有什么事吗？"
        
        # 问年龄
        if "年龄" in danmu or "几岁" in danmu:
            return "22岁~永远18！哈哈哈"
        
        # 夸赞
        if any(k in danmu for k in ["可爱", "好看", "漂亮", "厉害", "牛"]):
            return "谢谢夸奖~你也很棒的说！❤️"
        
        # 问游戏
        if "游戏" in danmu or "玩什么" in danmu:
            return "今天想玩点轻松的~大家想看什么？"
        
        # 问问题
        if "?" in danmu or "？" in danmu:
            return "这个问题问得好~让小悠想想..."
        
        # 默认回复
        responses = [
            "嗯嗯~说得对！",
            "哈哈哈好好玩~",
            "对对对，就是这样！",
            f"@{username} 说得不错嘛~",
            "小悠觉得可以！",
            "有道理！"
        ]
        return random.choice(responses)
    
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
    data = request.json
    result = run_async(liver.process_danmu_async(data))
    return jsonify({"success": True, "data": result})


@app.route("/api/welcome", methods=["POST"])
def welcome():
    """欢迎观众"""
    data = request.json
    username = data.get("username", "新朋友")
    result = run_async(liver.welcome_async(username))
    return jsonify({"success": True, "data": result})


@app.route("/api/tts", methods=["POST"])
def tts():
    """文字转语音"""
    data = request.json
    text = data.get("text", "")
    if not text:
        return jsonify({"success": False, "error": "文字不能为空"})
    
    result = run_async(liver.generate_tts(text))
    return jsonify({"success": True, "audio": result})


@app.route("/api/status", methods=["GET"])
def status():
    """状态查询"""
    return jsonify({
        "status": "running",
        "is_live": liver.is_live,
        "name": settings["name"]
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print(f"🤖 虚拟主播 [{settings['name']}] 服务启动中...")
    print(f"📁 音频输出目录: {AUDIO_DIR}")
    print(f"🔊 使用语音: {settings['voice']}")
    print("\nAPI接口:")
    print("  POST /api/danmu   - 接收弹幕，返回AI回复")
    print("  POST /api/welcome - 欢迎观众")
    print("  POST /api/tts     - 文字转语音")
    print("  GET  /api/status  - 查看状态")
    
    app.run(host="0.0.0.0", port=5001, debug=True)
