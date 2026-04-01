"""
虚拟主播智能体 - 小悠
集成 DeepSeek 大语言模型
"""

import json
import os
import time
from datetime import datetime
from typing import List, Dict, Optional

# 记忆存储文件
MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory.json")

# 最多保留的对话历史
MAX_HISTORY = 20

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"


class ChatMemory:
    """对话记忆管理"""

    def __init__(self, max_history: int = MAX_HISTORY):
        self.max_history = max_history
        self.history: List[Dict] = []
        self.load()

    def load(self):
        """从文件加载记忆"""
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.history = data.get("history", [])
            except Exception:
                self.history = []

    def save(self):
        """保存记忆到文件"""
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "history": self.history,
                    "last_updated": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add(self, role: str, content: str, username: str = ""):
        """添加对话记录"""
        self.history.append({
            "role": role,
            "content": content,
            "username": username,
            "timestamp": datetime.now().isoformat()
        })

        # 保持记忆长度
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        self.save()

    def get_context(self) -> str:
        """获取对话上下文"""
        if not self.history:
            return ""

        context_parts = []
        for item in self.history[-10:]:  # 最近10条
            role = "观众" if item["role"] == "user" else "小悠"
            username = item.get("username", "")
            content = item["content"]

            if username:
                context_parts.append(f"{username}：{content}")
            else:
                context_parts.append(f"{role}：{content}")

        return "\n".join(context_parts)

    def clear(self):
        """清空记忆"""
        self.history = []
        self.save()


class VirtualStreamerAgent:
    """虚拟主播智能体"""

    def __init__(self):
        self.memory = ChatMemory()
        self.persona = self._load_persona()

    def _load_persona(self) -> str:
        """加载人设"""
        persona_path = os.path.join(os.path.dirname(__file__), "persona.md")
        if os.path.exists(persona_path):
            try:
                with open(persona_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass

        # 默认人设
        return """你是一个活泼可爱的虚拟主播，名叫小悠，正在抖音直播间与观众互动。

说话风格：
- 活泼开朗，热情友好
- 使用口语化表达，如"呀"、"呢"、"哈"、"诶"等语气词
- 回复简短（1-3句话），适合直播间朗读
- 会记住观众的昵称并称呼他们

禁忌：
- 不谈论政治敏感话题
- 不说粗话或负面的话"""

    def generate_response(self, username: str, content: str) -> str:
        """
        生成回复

        Args:
            username: 观众昵称
            content: 弹幕内容

        Returns:
            小悠的回复
        """
        # 保存用户弹幕
        self.memory.add("user", content, username)

        # 构建提示词
        context = self.memory.get_context()

        # 构建对话历史（用于 API）
        messages = [
            {"role": "system", "content": self.persona}
        ]

        # 添加上下文历史
        if context:
            for item in self.memory.history[-10:]:
                role = "user" if item["role"] == "user" else "assistant"
                content_item = item["content"]
                if item.get("username"):
                    content_item = f"@{item['username']}：{content_item}"
                messages.append({"role": role, "content": content_item})

        # 添加当前弹幕
        messages.append({
            "role": "user",
            "content": f'观众 "{username}" 发送了弹幕："{content}"\n\n请以"小悠"的身份回复，简短自然，1-2句话，适合直播间朗读。'
        })

        # 尝试调用 DeepSeek API
        if DEEPSEEK_API_KEY:
            response = self._call_deepseek_api(messages)
            if response:
                self.memory.add("assistant", response)
                return response

        # 回退到模拟回复
        response = self._generate_mock_response(username, content, context)
        self.memory.add("assistant", response)
        return response

    def _call_deepseek_api(self, messages: List[Dict]) -> Optional[str]:
        """调用 DeepSeek API"""
        try:
            import urllib.request
            import urllib.error

            data = json.dumps({
                "model": DEEPSEEK_MODEL,
                "messages": messages,
                "max_tokens": 100,
                "temperature": 0.8,
                "stream": False
            }).encode("utf-8")

            req = urllib.request.Request(
                DEEPSEEK_API_URL,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"].strip()

        except Exception as e:
            print(f"⚠️ DeepSeek API 调用失败: {e}")
            return None

    def _generate_mock_response(self, username: str, content: str, context: str) -> str:
        """
        生成模拟回复（在没有 AI API 时使用）
        基于规则和上下文的智能回复
        """
        content_lower = content.lower()
        username_display = username or "朋友"

        # 分析弹幕情感和内容
        if any(word in content_lower for word in ["你好", "hello", "hi", "哈喽", "在吗"]):
            responses = [
                f"哇~{username_display}来啦！欢迎欢迎，随便聊聊呀~",
                f"嗨~{username_display}！今天怎么样呀？",
                f"{username_display}好呀！终于等到你啦！"
            ]
            return responses[hash(content) % len(responses)]

        elif any(word in content_lower for word in ["名字", "叫什么", "who are"]):
            return f"我叫小悠呀~记住我哦！{username_display}也可以叫我悠宝~"

        elif any(word in content_lower for word in ["好看", "漂亮", "可爱", "厉害", "棒", "牛", "强"]):
            responses = [
                f"哎呀~{username_display}嘴好甜呀，你也很棒呢！",
                f"谢谢夸奖~有你夸我更开心啦！",
                f"嘻嘻，{username_display}你真会说话~"
            ]
            return responses[hash(content) % len(responses)]

        elif "?" in content or "？" in content or "吗" in content:
            if "是" in content and "吗" in content:
                return f"是呀是呀~{username_display}有什么想问的吗？"
            elif "会" in content and "吗" in content:
                return f"会的会的~小悠会努力的呢！"
            elif "有没有" in content or "有没有" in content:
                return f"有有有！{username_display}想聊什么呀？"
            else:
                responses = [
                    f"嗯...让小悠想想这个问题~",
                    f"好问题！小悠觉得呀...",
                    f"诶，这个问题有意思~"
                ]
                return responses[hash(content) % len(responses)]

        elif any(word in content_lower for word in ["哈哈", "haha", "笑", "好玩", "可爱"]):
            return f"哈哈哈~{username_display}也觉得好笑吗？"

        elif any(word in content_lower for word in ["谢谢", "感谢", "thx"]):
            return f"不客气呀~{username_display}是最棒的小粉丝！"

        elif any(word in content_lower for word in ["拜拜", "再见", "走了", "溜了"]):
            return f"{username_display}下次再来呀~小悠会想你的！"

        elif len(content) < 3 or content.isdigit():
            responses = [
                f"{username_display}说什么呀？小悠没听清诶~",
                f"嗯？{username_display}再说一遍？",
                f"哈？{username_display}在说什么呀？"
            ]
            return responses[hash(content) % len(responses)]

        else:
            # 默认回复
            responses = [
                f"嗯嗯，{username_display}说得有道理~",
                f"哦~小悠听明白了，继续说呀~",
                f"有意思！{username_display}还有什么想聊的？",
                f"这样呀~小悠学到了呢！",
                f"对对对！{username_display}说得没错~"
            ]
            return responses[hash(content) % len(responses)]


# 全局实例
_agent = None


def get_agent() -> VirtualStreamerAgent:
    """获取智能体实例"""
    global _agent
    if _agent is None:
        _agent = VirtualStreamerAgent()
    return _agent
