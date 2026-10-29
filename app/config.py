# -*- coding: utf-8 -*-
"""全局配置：读取 .env，对应 Java 的 application.properties / application.yml"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # DashScope (通义)
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY")
    dashscope_chat_model: str = "qwen-plus"
    dashscope_embedding_model: str = "text-embedding-v2"

    # DeepSeek
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY")
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_chat_model: str = "deepseek-chat"

    # 各 ChatClient 温度（复刻 ChatClientInitConfiguration）
    planning_temperature: float = 0.1
    bot_temperature: float = 1.2
    knowledge_temperature: float = 0.7

    # 增量记忆保留条数（复刻 IncrementalChatMemory.lastN）
    memory_last_n: int = 10

    # MySQL（历史消息持久化）
    mysql_url: str = "mysql+pymysql://root:123456@localhost:3306/spring_ai?charset=utf8mb4"
    mysql_chat_memory_table: str = "python_ai_chat_memory"


@lru_cache
def get_settings() -> Settings:
    return Settings()
