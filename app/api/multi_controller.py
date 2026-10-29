# -*- coding: utf-8 -*-
"""规划/多 ChatClient 接口，复刻 controller/MultiChatClientController.java
GET /api/multi/chat?message=&sessionId= -> 流式文本
"""
import uuid
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agents import planner

router = APIRouter(prefix="/api/multi", tags=["multi"])


@router.get("/chat")
async def chat(message: str = "", sessionId: Optional[str] = None) -> StreamingResponse:  # noqa: N803
    session_id = sessionId or str(uuid.uuid4())
    return StreamingResponse(
        planner.stream_chat(message, session_id),
        media_type="text/stream;charset=UTF-8",
    )
