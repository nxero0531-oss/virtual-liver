"""
抖音云弹幕接入模块
通过WebSocket连接抖音云服务，接收实时弹幕
"""

import json
import asyncio
import websockets
from pathlib import Path

# 抖音云 WebSocket 地址 (需要替换为你的实际地址)
DOUYIN_WS_URL = "wss://cloud.douyin.com"

# 回调地址配置
CALLBACK_CONFIG = {
    "type": "broadcast",
    "event": ["live_comment", "live_enter", "live_like", "live_gift"]
}


class DouyinConnector:
    """抖音云连接器"""
    
    def __init__(self, backend_url: str = "http://localhost:5001"):
        self.backend_url = backend_url
        self.ws_url = None
        self.is_connected = False
        self.access_token = None  # 需要从抖音云获取
        self.room_id = None       # 直播间ID
        
    def set_credentials(self, access_token: str, room_id: str):
        """设置抖音云凭证"""
        self.access_token = access_token
        self.room_id = room_id
        self.ws_url = f"{DOUYIN_WS_URL}?token={access_token}&room_id={room_id}"
    
    async def connect(self):
        """连接到抖音云"""
        if not self.ws_url:
            raise ValueError("请先调用 set_credentials() 设置凭证")
        
        try:
            async with websockets.connect(self.ws_url) as ws:
                self.is_connected = True
                print(f"✅ 已连接到抖音云 (房间: {self.room_id})")
                
                # 发送订阅请求
                await ws.send(json.dumps(CALLBACK_CONFIG))
                
                # 持续接收消息
                async for message in ws:
                    await self.handle_message(message)
                    
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            self.is_connected = False
    
    async def handle_message(self, message: str):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            msg_type = data.get("event_type", "")
            
            if msg_type == "live_comment":
                # 弹幕消息
                danmu_data = {
                    "user_id": data.get("user", {}).get("open_id", "unknown"),
                    "username": data.get("user", {}).get("nickname", "观众"),
                    "content": data.get("comment", "")
                }
                await self.send_to_backend("/api/danmu", danmu_data)
                
            elif msg_type == "live_enter":
                # 用户进入
                username = data.get("user", {}).get("nickname", "新朋友")
                await self.send_to_backend("/api/welcome", {"username": username})
                
            elif msg_type == "live_gift":
                # 收到礼物
                gift_name = data.get("gift_name", "礼物")
                username = data.get("user", {}).get("nickname", "观众")
                print(f"🎁 {username} 送出了 {gift_name}")
                
            elif msg_type == "live_like":
                # 收到点赞
                print(f"❤️ 收到点赞")
                
        except json.JSONDecodeError:
            print(f"收到非JSON消息: {message[:100]}")
        except Exception as e:
            print(f"处理消息出错: {e}")
    
    async def send_to_backend(self, endpoint: str, data: dict):
        """发送数据到本地后端"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"{self.backend_url}{endpoint}"
                async with session.post(url, json=data) as resp:
                    result = await resp.json()
                    print(f"🤖 AI回复: {result.get('data', {}).get('text', '')}")
        except Exception as e:
            print(f"发送失败: {e}")
    
    async def run(self):
        """运行连接"""
        if not self.access_token or not self.room_id:
            print("⚠️ 请先设置 access_token 和 room_id")
            print("   connector.set_credentials('你的token', '你的房间号')")
            return
        
        await self.connect()


# 独立运行测试
if __name__ == "__main__":
    import sys
    
    connector = DouyinConnector()
    
    if len(sys.argv) >= 3:
        # 命令行参数: python douyin_connector.py <token> <room_id>
        token = sys.argv[1]
        room_id = sys.argv[2]
        connector.set_credentials(token, room_id)
        asyncio.run(connector.run())
    else:
        print("""
抖音云弹幕接入
用法: python douyin_connector.py <access_token> <room_id>

请先在抖音云后台获取:
1. Access Token (用于API认证)
2. Room ID (直播间ID)

获取步骤:
1. 访问 https://cloud.douyin.com
2. 进入你的应用
3. 获取 Access Token (需要调用 OAuth 接口)
4. 使用直播伴侣开播，获取房间ID
        """)
