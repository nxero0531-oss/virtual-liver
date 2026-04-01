#!/usr/bin/env python3
"""获取抖音云 Access Token"""

import requests

# 凭证
CLIENT_KEY = "ttd170a7cd4f1184fb10"
CLIENT_SECRET = "86acb22a4003dd831d66aee0e8a11fb995315e5e"

# 获取 Client Token
url = "https://open-sandbox.douyin.com/oauth/client_token"
data = {
    "client_key": CLIENT_KEY,
    "client_secret": CLIENT_SECRET,
    "grant_type": "client_token"
}

print("正在获取 Access Token...")
response = requests.post(url, data=data)
result = response.json()

print("\n响应状态码:", response.status_code)
print("响应内容:", response.text[:500] if response.text else "空")

if result.get("data") and result["data"].get("access_token"):
    token = result["data"]["access_token"]
    print(f"\n✅ 获取成功！")
    print(f"Access Token: {token}")
    
    # 保存到文件
    with open("douyin_token.txt", "w") as f:
        f.write(token)
    print("Token 已保存到 douyin_token.txt")
else:
    print("\n❌ 获取失败，请检查凭证是否正确")
    if result.get("message"):
        print(f"错误信息: {result['message']}")
