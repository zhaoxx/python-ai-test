# -*- coding: utf-8 -*-
"""FastAPI 应用入口，对应 SpringAiTestApplication.java + 各 Controller 的路由聚合"""
from fastapi import FastAPI

from app.api import (
    customer_controller,
    knowledge_controller,
    model_controller,
    multi_controller,
)

app = FastAPI(title="python-ai-test", description="AI agent 测试项目")

# 挂载 4 个 Controller 对应的路由
app.include_router(customer_controller.router)
app.include_router(knowledge_controller.router)
app.include_router(multi_controller.router)
app.include_router(model_controller.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
