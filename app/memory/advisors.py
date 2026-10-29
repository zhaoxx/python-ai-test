# -*- coding: utf-8 -*-
"""Advisor 复刻：
- MessageIdInjectionAdvisor: 为 user/assistant 消息注入 message_id（存储层已处理，这里提供显式工具函数）
- ReAgainAdvisor: 在用户文本后追加"再思考一下"提示
"""
import uuid
from typing import List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def inject_message_ids(messages: List[BaseMessage]) -> List[BaseMessage]:
    """对应 MessageIdInjectionAdvisor.before/after：给缺 message_id 的消息补 UUID。"""
    for m in messages:
        if isinstance(m, (HumanMessage, AIMessage)):
            additional = dict(getattr(m, "additional_kwargs", {}) or {})
            if not additional.get("message_id"):
                additional["message_id"] = str(uuid.uuid4())
                m.additional_kwargs = additional
    return messages


# 对应 ReAgainAdvisor.DEFAULT_USER_TEXT_ADVISE
RE_AGAIN_TEMPLATE = "{user_input_text}\n再思考一下上个问题：{user_input_text}"


def re_again(text: str) -> str:
    """对应 ReAgainAdvisor.before：把用户输入包装成"二次思考"提示。"""
    return RE_AGAIN_TEMPLATE.format(user_input_text=text)
