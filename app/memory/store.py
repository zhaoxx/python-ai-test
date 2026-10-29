# -*- coding: utf-8 -*-
"""对话记忆门面：默认走 MySQL 持久化。

历史行为：
- 早期为进程内内存存储（参考 IncrementalChatMemory.java）
- 现在切换为基于 MySQL 的持久化（IncrementalJdbcChatMemoryRepository）

对外 API 保持不变：
- get_history(conversation_id) -> BaseChatMessageHistory
- get(conversation_id) -> List[BaseMessage]  （截断到最后 last_n 条）
- clear(conversation_id)
"""
from typing import Dict, List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage

from app.config import get_settings
from app.memory.mysql_store import MySQLChatMessageHistory


class ChatMemoryStore:
    """对应 Spring 的 ChatMemoryRepository：会话隔离 + last_n 截断。"""

    def __init__(self):
        self._cache: Dict[str, MySQLChatMessageHistory] = {}
        self.last_n = get_settings().memory_last_n

    def get_history(self, conversation_id: str) -> BaseChatMessageHistory:
        """作为 RunnableWithMessageHistory 的 get_session_history 回调。"""
        history = self._cache.get(conversation_id)
        if history is None:
            history = MySQLChatMessageHistory(conversation_id)
            self._cache[conversation_id] = history
        return history

    def get(self, conversation_id: str) -> List[BaseMessage]:
        msgs = self.get_history(conversation_id).messages
        if self.last_n > 0 and len(msgs) > self.last_n:
            return msgs[-self.last_n:]
        return list(msgs)

    def clear(self, conversation_id: str) -> None:
        self.get_history(conversation_id).clear()


# 全局单例
chat_memory_store = ChatMemoryStore()
