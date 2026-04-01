# 虚拟主播系统 - 抖音接入指南

## 当前状态

✅ 基础服务已搭建完成
⏳ 等待抖音云配置

---

## 接入抖音云步骤

### 第一阶段：获取凭证（需要你做）

#### 1. 登录抖音云控制台
访问: https://cloud.douyin.com

#### 2. 获取 Access Token

抖音云需要 OAuth 2.0 认证来获取 Token。步骤如下：

1. 在抖音云后台创建应用后
2. 获取 `Client Key` 和 `Client Secret`
3. 调用 OAuth 接口获取 Access Token

**OAuth 接口地址：**
```
https://open.douyin.com/oauth/client_token
```

**请求参数：**
| 参数 | 值 |
|------|-----|
| client_key | 你的 Client Key |
| client_secret | 你的 Client Secret |
| grant_type | client_token |

#### 3. 获取直播间 Room ID

当你用直播伴侣开播时，会生成一个 Room ID。

---

### 第二阶段：配置本地服务（我来帮你）

拿到 Token 和 Room ID 后，告诉我，我来帮你：
1. 配置连接参数
2. 启动弹幕监听
3. 测试完整流程

---

## 快速测试

在等待抖音云配置期间，可以先用本地模拟器测试：

```bash
cd ~/WorkBuddy/20260401102950/virtual-liver
source venv/bin/activate
python scripts/test_danmu.py
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `backend/main.py` | 核心服务（AI对话 + TTS） |
| `backend/douyin_connector.py` | 抖音云接入模块 |
| `config/persona.md` | 虚拟主播人设 |
| `config/settings.json` | 基础设置 |
| `scripts/test_danmu.py` | 本地测试工具 |

---

## 常见问题

**Q: 实名认证需要多久？**
A: 通常几分钟到几小时，个别情况可能需要1-2天。

**Q: Access Token 会过期吗？**
A: 会，抖音云的 Token 有有效期，记得定期刷新。

**Q: 能否不用抖音云直接接弹幕？**
A: 可以用第三方弹幕工具，但稳定性较差。
