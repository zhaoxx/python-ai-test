# -*- coding: utf-8 -*-
"""MySQL 引擎/会话工厂，复刻 Spring DataSource 角色。

- 通过 SQLAlchemy 创建 engine，懒加载 + 进程内单例
- 启动时自动建表（CREATE TABLE IF NOT EXISTS，与 sql/schema-mysql.sql 等价）
"""
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings


DDL_TEMPLATE = """
CREATE TABLE IF NOT EXISTS `{table}` (
   `id` bigint NOT NULL AUTO_INCREMENT,
   `conversation_id` varchar(36) NOT NULL,
   `content` longtext NOT NULL,
   `type` varchar(20) NOT NULL,
   `timestamp` timestamp NOT NULL,
   `message_id` varchar(36) NOT NULL DEFAULT '' COMMENT '消息唯一标识',
   PRIMARY KEY (`id`),
   KEY `idx_conversation_id_timestamp` (`conversation_id`,`timestamp`),
   KEY `uk_message_id` (`message_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
"""


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        settings.mysql_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        future=True,
    )


@lru_cache
def get_session_factory():
    return sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)


def ensure_table() -> None:
    """启动时确保表存在；如 MySQL 不可达则打印警告并跳过。"""
    settings = get_settings()
    ddl = DDL_TEMPLATE.format(table=settings.mysql_chat_memory_table)
    try:
        with get_engine().begin() as conn:
            conn.execute(text(ddl))
    except Exception as exc:  # pragma: no cover
        # 不让建表失败影响服务启动，仅在调用时再暴露异常
        print(f"[mysql] ensure_table failed: {exc}")
