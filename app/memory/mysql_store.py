# -*- coding: utf-8 -*-
"""MySQL 版对话记忆，复刻 IncrementalJdbcChatMemoryRepository.java

特性：
- 按 conversation_id 隔离
- 写入前为缺失 message_id 的消息注入 UUID
- 基于 message_id 去重，仅追加新消息
- type 字段映射 LangChain 消息类型：human / ai / system
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from sqlalchemy import text

from app.config import get_settings
from app.memory.db import get_session_factory


TYPE_MAP = {
    "human": HumanMessage,
    "ai": AIMessage,
    "system": SystemMessage,
}


def _message_type_name(message: BaseMessage) -> str:
    """LangChain 消息类型 → 数据库 type 字段。"""
    if isinstance(message, HumanMessage):
        return "human"
    if isinstance(message, AIMessage):
        return "ai"
    if isinstance(message, SystemMessage):
        return "system"
    return type(message).__name__.lower()


def _row_to_message(row) -> BaseMessage:
    msg_cls = TYPE_MAP.get(row.type, HumanMessage)
    additional: Dict = {"message_id": row.message_id}
    if row.timestamp is not None:
        additional["timestamp"] = row.timestamp.isoformat()
    return msg_cls(content=row.content, additional_kwargs=additional)


class MySQLChatMessageHistory(BaseChatMessageHistory):
    """单个 conversation_id 的 MySQL 持久化记忆。"""

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.table = get_settings().mysql_chat_memory_table

    # ---------- 读 ----------
    @property
    def messages(self) -> List[BaseMessage]:  # type: ignore[override]
        sql = text(
            f"SELECT content, type, `timestamp`, message_id "
            f"FROM `{self.table}` "
            f"WHERE conversation_id = :cid ORDER BY id ASC"
        )
        with get_session_factory()() as session:
            rows = session.execute(sql, {"cid": self.conversation_id}).fetchall()
        return [_row_to_message(r._mapping) for r in rows]

    # ---------- 写（增量去重） ----------
    def add_messages(self, messages: List[BaseMessage]) -> None:
        if not messages:
            return
        # 1. 注入 message_id
        prepared: List[BaseMessage] = []
        for msg in messages:
            additional = dict(getattr(msg, "additional_kwargs", {}) or {})
            if not additional.get("message_id"):
                additional["message_id"] = str(uuid.uuid4())
                msg.additional_kwargs = additional
            prepared.append(msg)

        # 2. 已存在的 message_id（用于去重，等价 IncrementalJdbcChatMemoryRepository）
        sql_exists = text(
            f"SELECT message_id FROM `{self.table}` WHERE conversation_id = :cid"
        )
        sql_insert = text(
            f"INSERT INTO `{self.table}` "
            f"(conversation_id, content, type, `timestamp`, message_id) "
            f"VALUES (:cid, :content, :type, :ts, :mid)"
        )
        with get_session_factory()() as session:
            existing = {r[0] for r in session.execute(sql_exists, {"cid": self.conversation_id}).fetchall()}
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            for msg in prepared:
                mid = msg.additional_kwargs["message_id"]
                if mid in existing:
                    continue
                session.execute(
                    sql_insert,
                    {
                        "cid": self.conversation_id,
                        "content": str(msg.content),
                        "type": _message_type_name(msg),
                        "ts": now,
                        "mid": mid,
                    },
                )
                existing.add(mid)
            session.commit()

    def add_message(self, message: BaseMessage) -> None:
        self.add_messages([message])

    # ---------- 清空 ----------
    def clear(self) -> None:
        sql = text(f"DELETE FROM `{self.table}` WHERE conversation_id = :cid")
        with get_session_factory()() as session:
            session.execute(sql, {"cid": self.conversation_id})
            session.commit()
