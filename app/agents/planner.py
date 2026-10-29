# -*- coding: utf-8 -*-
"""规划 Agent，复刻 controller/MultiChatClientController.java
+ config/ChatClientInitConfiguration.java（planningChatClient / botChatClient）

流程：
1) planningChatClient 以低温度输出结构化 AIJob（jobType/orderNo/name）
2) 按 jobType 分流：CANCEL / QUERY 走业务判断；OTHER 交给 botChatClient 流式回复
3) 全程以生成器产出 SSE 文本，等价 Java 的 Sinks.Many + Flux
"""
from typing import AsyncIterator, List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory

from app.config import get_settings
from app.llm.providers import build_chat_model
from app.memory.store import chat_memory_store
from app.models.schemas import AIJob, JobType

PLANNING_SYSTEM = """# 票务助手任务分拆规则
## 1. 要求
### 1.1 根据用户内容识别任务

## 2. 任务
### 2.1 JobType:退票(CANCEL) 要求用户提供姓名和预订号，或者从对话记忆中查找
### 2.2 JobType:查票(QUERY) 要求用户提供预定号，或者从对话记忆中查找
### 2.3 JobType:其他(OTHER)
"""

BOT_SYSTEM = "你是DF航空智能客服代理，请以友好、热情的服务用户。"


def _build_planner():
    settings = get_settings()
    model = build_chat_model("deepseek", temperature=settings.planning_temperature)
    return model.with_structured_output(AIJob)


def _build_bot_chain():
    settings = get_settings()
    model = build_chat_model("deepseek", temperature=settings.bot_temperature)
    prompt = ChatPromptTemplate.from_messages(
        [("system", BOT_SYSTEM), ("placeholder", "{chat_history}"), ("human", "{input}")]
    )
    chain = prompt | model
    return RunnableWithMessageHistory(
        chain,
        lambda session_id: chat_memory_store.get_history(session_id),
        input_messages_key="input",
        history_messages_key="chat_history",
    )


_planner = None
_bot = None


def _get_planner():
    global _planner
    if _planner is None:
        _planner = _build_planner()
    return _planner


def _get_bot():
    global _bot
    if _bot is None:
        _bot = _build_bot_chain()
    return _bot


async def _plan(message: str, session_id: str) -> AIJob:
    """带记忆的规划：把历史消息一并送入结构化输出模型。"""
    history: List[BaseMessage] = chat_memory_store.get(session_id)
    msgs: List[BaseMessage] = [SystemMessage(content=PLANNING_SYSTEM)]
    msgs.extend(history)
    msgs.append(HumanMessage(content=message))
    # 记录本轮 user 消息到记忆
    chat_memory_store.get_history(session_id).add_messages([HumanMessage(content=message)])
    return await _get_planner().ainvoke(msgs)


async def stream_chat(message: str, session_id: str) -> AsyncIterator[str]:
    """对应 MultiChatClientController.chat，返回文本流。"""
    yield "正在规划任务...<br/>"

    job = await _plan(message, session_id)

    if job.jobType == JobType.CANCEL:
        if not job.orderNo or not job.name:
            yield "请输入姓名和订单号"
        else:
            yield "退票成功"
    elif job.jobType == JobType.QUERY:
        if not job.orderNo:
            yield "请输入订单号"
        else:
            yield "正在查询订单信息...<br/>"
    elif job.jobType == JobType.OTHER:
        bot = _get_bot()
        config = {"configurable": {"session_id": session_id}}
        async for chunk in bot.astream({"input": message}, config=config):
            text = getattr(chunk, "content", None)
            if text:
                yield text
            # 流结束时 RunnableWithMessageHistory 会自动写入 AI 回复
        else:
            # 保底：a-stream 的 dict 形式取 message
            pass
    else:
        yield "解析异常"
