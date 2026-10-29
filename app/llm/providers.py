# -*- coding: utf-8 -*-
"""LLM Provider：构造 DashScope / DeepSeek 模型实例，对应 Java 的 ChatModel Bean 与 modelMap"""
from functools import lru_cache

from app.config import get_settings


def build_chat_model(platform: str, model: str | None = None, temperature: float | None = None):
    """根据平台名构造一个 chat 模型实例。

    对应 MorePlatformAndModelController 里 modelMap.get(platform) + 动态 options。
    """
    settings = get_settings()
    platform = (platform or "deepseek").lower()

    if platform == "deepseek":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model=model or settings.deepseek_chat_model,
            temperature=temperature if temperature is not None else 0.7,
            streaming=True,
        )

    # 默认走 DashScope（通义）
    from langchain_community.chat_models.tongyi import ChatTongyi

    return ChatTongyi(
        dashscope_api_key=settings.dashscope_api_key,
        model=model or settings.dashscope_chat_model,
        temperature=temperature if temperature is not None else 0.7,
        streaming=True,
    )


@lru_cache
def get_embeddings():
    """DashScope 文本向量化模型，对应 spring.ai.dashscope.embedding。"""
    from langchain_community.embeddings import DashScopeEmbeddings

    settings = get_settings()
    return DashScopeEmbeddings(
        dashscope_api_key=settings.dashscope_api_key,
        model=settings.dashscope_embedding_model,
    )
