# -*- coding: utf-8 -*-
"""静态工具，复刻 tools/OrderTools.java（@Tool 注解 → @tool 装饰器）"""
from langchain_core.tools import tool


@tool
def query_order(orderId: str) -> str:  # noqa: N803 参数名与 Java/模型 schema 对齐
    """根据订单号查询订单状态、商品明细和收货地址。"""
    # 实际开发中这里调用数据库或微服务
    if orderId.startswith("abc"):
        return f"订单 {orderId} 状态为：待发货"
    return f"订单 {orderId} 状态为：已发货，商品：[蓝牙耳机x1]，预计明天送达。"


@tool
def cancel_order(orderId: str) -> str:  # noqa: N803
    """根据订单号取消订单。仅当订单处于'待发货'状态时允许取消。"""
    # 实际开发中需做严格的幂等和状态校验
    if orderId == "abc":
        raise RuntimeError("参数异常")
    return f"订单 {orderId} 已成功取消，款项将在1-3个工作日内原路退回。"


# 对应 SmartCustomerServiceImpl 中被注释掉的 .defaultTools(orderTools)
order_tools = [query_order, cancel_order]
