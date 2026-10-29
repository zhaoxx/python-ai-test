# -*- coding: utf-8 -*-
"""内存版增量对话记忆，复刻 config/IncrementalChatMemory.java + IncrementalJdbcChatMemoryRepository.java

核心行为对齐：
- 按 conversation_id 隔离会话
- add 时用 message_id 去重（无 id 则用 "类型:内容" 兜底指纹），仅追加"未存储过"的新消息
- 存储前为缺失 message_id 的消息注入 UUID
- get 返回最后 last_n 条
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage

from app.config import get_settings


def _message_key(message: BaseMessage) -> str:
    """复刻 extractMessageKey：优先 message_id，否则 类型:内容 指纹。"""
    additional = getattr(message, "additional_kwargs", {}) or {}
    mid = additional.get("message_id")
    if mid:
        return str(mid)
    return f"{type(message).__name__}:{message.content}"


def _ensure_message_id(message: BaseMessage) -> BaseMessage:
    """复刻 ensureMessageId：没有 message_id 就注入 UUID。"""
    additional = dict(getattr(message, "additional_kwargs", {}) or {})
    if additional.get("message_id"):
        return message
    new_id = str(uuid.uuid4())
    additional["message_id"] = new_id
    message.additional_kwargs = additional
    return message


class InMemoryIncrementalChatMessageHistory(BaseChatMessageHistory):
    """单个 conversation_id 的增量记忆。"""

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.messages: List[BaseMessage] = []

    def add_messages(self, messages: List[BaseMessage]) -> None:
        existing_keys = {_message_key(m) for m in self.messages}
        for msg in messages:
            msg = _ensure_message_id(msg)
            key = _message_key(msg)
            if key not in existing_keys:
                # 附加时间戳，方便排序/调试
                msg.additional_kwargs.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
                self.messages.append(msg)
                existing_keys.add(key)

    def clear(self) -> None:
        # 复刻 deleteByConversationId（增量模式默认不清空，除非显式调用）
        self.messages = []


class ChatMemoryStore:
    """对应 Spring 的 ChatMemoryRepository：全局会话表 + last_n 截断。"""

    def __init__(self):
        self._histories: Dict[str, InMemoryIncrementalChatMessageHistory] = {}
        self.last_n = get_settings().memory_last_n

    def get_history(self, conversation_id: str) -> BaseChatMessageHistory:
        """作为 RunnableWithMessageHistory 的 get_session_history 回调。"""
        if conversation_id not in self._histories:
            self._histories[conversation_id] = InMemoryIncrementalChatMessageHistory(conversation_id)
        return self._histories[conversation_id]

    def get(self, conversation_id: str) -> List[BaseMessage]:
        history = self.get_history(conversation_id)
        msgs = history.messages
        if self.last_n > 0 and len(msgs) > self.last_n:
            return msgs[-self.last_n:]
        return list(msgs)

    def clear(self, conversation_id: str) -> None:
        if conversation_id in self._histories:
            self._histories[conversation_id].clear()


# 全局单例（进程内内存存储，对应"全内存化"）
chat_memory_store = ChatMemoryStore()
