# -*- coding: utf-8 -*-
"""多平台/多模型接口，复刻 controller/MorePlatformAndModelController.java
GET /chat?message=&plaform=&model=&temperature= -> 流式文本
"""
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.llm.providers import build_chat_model

router = APIRouter(tags=["model"])


async def _stream(message: str, plaform: str, model: Optional[str], temperature: Optional[float]):
    chat_model = build_chat_model(plaform, model=model, temperature=temperature)
    async for chunk in chat_model.astream([HumanMessage(content=message)]):
        text = getattr(chunk, "content", None)
        if text:
            yield text


@router.get("/chat")
async def chat(
    message: str = "",
    plaform: str = "dashscope",  # noqa: N803 保持与 Java 一致（原字段拼写）
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> StreamingResponse:
    return StreamingResponse(
        _stream(message, plaform, model, temperature),
        media_type="text/stream;charset=UTF-8",
    )
