#!/usr/bin/env python3
"""
模拟弹幕测试工具
用于测试虚拟主播的对话和语音功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_status():
    """测试服务状态"""
    resp = requests.get(f"{BASE_URL}/api/status")
    print(f"\n📊 服务状态: {resp.json()}\n")

def test_tts():
    """测试语音合成"""
    print("🎤 测试语音合成...")
    test_texts = [
        "大家好~我是小悠，今天来陪大家玩啦！",
        "欢迎新朋友进入直播间~",
        "谢谢你的夸奖，你也很棒的说！"
    ]
    
    for text in test_texts:
        resp = requests.post(f"{BASE_URL}/api/tts", json={"text": text})
        result = resp.json()
        if result["success"]:
            print(f"  ✅ {text}")
            print(f"     音频: {result['audio']}")
        else:
            print(f"  ❌ 失败: {result['error']}")
        time.sleep(0.5)

def test_danmu():
    """测试弹幕处理"""
    print("\n💬 测试弹幕处理...")
    test_danmus = [
        {"user_id": "u1", "username": "小明", "content": "你好呀"},
        {"user_id": "u2", "username": "小红", "content": "主播叫什么名字？"},
        {"user_id": "u3", "username": "游戏达人", "content": "你好可爱啊"},
        {"user_id": "u4", "username": "新观众", "content": "今天玩什么游戏？"},
        {"user_id": "u5", "username": "老粉", "content": "666"},
    ]
    
    for danmu in test_danmus:
        resp = requests.post(f"{BASE_URL}/api/danmu", json=danmu)
        result = resp.json()
        if result["success"]:
            data = result["data"]
            print(f"\n  📨 弹幕: {danmu['username']}: {danmu['content']}")
            print(f"  🤖 回复: {data['text']}")
            print(f"  🔊 音频: {data['audio']}")
        time.sleep(0.3)

def test_welcome():
    """测试欢迎"""
    print("\n👋 测试欢迎功能...")
    resp = requests.post(f"{BASE_URL}/api/welcome", json={"username": "测试观众"})
    result = resp.json()
    if result["success"]:
        data = result["data"]
        print(f"  🤖 欢迎语: {data['text']}")
        print(f"  🔊 音频: {data['audio']}")

def interactive_mode():
    """交互模式"""
    print("\n" + "="*50)
    print("🎮 交互模式 - 输入弹幕测试 (输入 q 退出)")
    print("="*50 + "\n")
    
    while True:
        try:
            danmu = input("💬 请输入弹幕内容: ").strip()
            if danmu.lower() == "q":
                print("👋 退出测试")
                break
            
            username = input("👤 请输入用户名 (默认: 测试用户): ").strip() or "测试用户"
            
            resp = requests.post(f"{BASE_URL}/api/danmu", json={
                "user_id": "test",
                "username": username,
                "content": danmu
            })
            result = resp.json()
            
            if result["success"]:
                data = result["data"]
                print(f"\n  🤖 小悠回复: {data['text']}")
                print(f"  🔊 音频文件: {data['audio']}")
            else:
                print(f"  ❌ 错误: {result.get('error', '未知错误')}")
            print()
            
        except KeyboardInterrupt:
            print("\n👋 退出测试")
            break

if __name__ == "__main__":
    print("🎯 虚拟主播测试工具")
    print("-" * 30)
    
    try:
        test_status()
        test_tts()
        test_danmu()
        test_welcome()
        interactive_mode()
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务，请确保后端服务已启动")
        print("   运行命令: source venv/bin/activate && python backend/main.py")
    except Exception as e:
        print(f"❌ 错误: {e}")
