# -*- coding: utf-8 -*-
"""动态工具，复刻 tools/DynamicToolService.java

Java 通过反射 + 手写 JSON Schema 动态构建 ToolCallback；
Python 用 StructuredTool.from_function + args_schema 等价实现，
并保留"从配置(schema) 动态构建工具列表"的模式（模拟从 DB 读取）。
"""
from typing import List

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field


def _query_order(orderId: str) -> str:  # noqa: N803
    if orderId.startswith("abc"):
        return f"订单 {orderId} 状态为：待发货"
    return f"订单 {orderId} 状态为：已发货，商品：[蓝牙耳机x1]，预计明天送达。"


def _cancel_order(orderId: str, name: str) -> str:  # noqa: N803
    if orderId == "abc":
        raise RuntimeError("参数异常")
    return f"订单 {orderId} 已成功取消，款项将在1-3个工作日内原路退回。"


class CancelOrderInput(BaseModel):
    """对应 cancelOrder 的 inputSchema：required = [orderId, name]"""
    orderId: str = Field(..., description="订单ID")  # noqa: N815
    name: str = Field(..., description="真实人名")


class QueryOrderInput(BaseModel):
    """对应 queryOrder 的 inputSchema：required = [orderId]"""
    orderId: str = Field(..., description="订单ID")  # noqa: N815
    name: str = Field(default="", description="真实人名")


class DynamicToolService:
    def get_tools(self) -> List[BaseTool]:
        return [self._get_cancel_order_tool(), self._get_query_order_tool()]

    def _get_cancel_order_tool(self) -> BaseTool:
        # 对应从 DB 读取 toolName/description/schema，再反射绑定方法
        return StructuredTool.from_function(
            func=_cancel_order,
            name="cancelOrder",
            description=(
                "根据订单号取消订单。仅当订单处于'待发货'状态时允许取消。"
                "需要传入一个包含 orderId(订单ID) 和 name(真实人名) 的JSON对象。"
            ),
            args_schema=CancelOrderInput,
        )

    def _get_query_order_tool(self) -> BaseTool:
        return StructuredTool.from_function(
            func=_query_order,
            name="queryOrder",
            description=(
                "根据订单号查询订单状态、商品明细和收货地址。"
                "需要传入一个包含 orderId(订单ID) 的JSON对象。"
            ),
            args_schema=QueryOrderInput,
        )


dynamic_tool_service = DynamicToolService()
