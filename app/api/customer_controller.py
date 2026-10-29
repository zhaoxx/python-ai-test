# -*- coding: utf-8 -*-
"""智能客服接口，复刻 controller/CustomerServiceController.java
GET /api/customer/chat?message=&sessionId=  -> 流式文本
"""
import uuid
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agents import customer as customer_agent

router = APIRouter(prefix="/api/customer", tags=["customer"])


@router.get("/chat")
async def chat(message: str = "", sessionId: Optional[str] = None) -> StreamingResponse:  # noqa: N803
    session_id = sessionId or str(uuid.uuid4())
    return StreamingResponse(
        customer_agent.stream_chat(message, session_id),
        media_type="text/stream;charset=UTF-8",
    )
