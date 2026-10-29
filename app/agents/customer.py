# -*- coding: utf-8 -*-
"""智能客服 Agent，复刻 service/impl/SmartCustomerServiceImpl.java

- defaultSystem：客服人设提示词（原文搬运）
- defaultAdvisors：多轮记忆（LangGraph MemorySaver ≈ PromptChatMemoryAdvisor）
- defaultToolCallbacks：动态工具 queryOrder/cancelOrder
- chat()：按 conversationId 隔离记忆并流式返回
"""
from typing import AsyncIterator

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from app.config import get_settings
from app.llm.providers import build_chat_model
from app.tools.dynamic_tools import dynamic_tool_service

SYSTEM_PROMPT = """您是电商平台的专属智能客服。请以友好、专业的语气回复。
在查询或取消订单前，必须先向用户确认订单号。
如果用户要求取消订单，请明确告知退款规则。
请始终使用中文回复。
"""

# 进程内记忆存储，等价 ChatMemory（按 thread_id=sessionId 隔离会话）
_checkpointer = MemorySaver()


def _build_agent():
    settings = get_settings()
    model = build_chat_model("dashscope", temperature=settings.bot_temperature)
    return create_react_agent(
        model=model,
        tools=dynamic_tool_service.get_tools(),
        checkpointer=_checkpointer,
        prompt=SYSTEM_PROMPT,
    )


_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = _build_agent()
    return _agent


async def stream_chat(message: str, conversation_id: str) -> AsyncIterator[str]:
    """对应 SmartCustomerService.chat 返回 Flux<String>。"""
    agent = get_agent()
    config = {"configurable": {"thread_id": conversation_id}}
    inputs = {"messages": [HumanMessage(content=message)]}
    async for chunk, _meta in agent.astream(inputs, config=config, stream_mode="messages"):
        text = getattr(chunk, "content", None)
        if text:
            yield text
