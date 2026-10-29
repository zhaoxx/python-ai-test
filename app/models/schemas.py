# -*- coding: utf-8 -*-
"""数据模型：对应 Java 的 CustomerOptions / MorePlatformAndModelOptions / AIJob"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CustomerOptions(BaseModel):
    """对应 model/CustomerOptions.java"""
    message: str = ""
    sessionId: Optional[str] = None  # noqa: N815 保持与 Java 端一致的查询参数名


class MorePlatformAndModelOptions(BaseModel):
    """对应 model/MorePlatformAndModelOptions.java（注意 Java 原字段拼写为 plaform）"""
    plaform: str = "dashscope"  # noqa: N815
    model: Optional[str] = None
    temperature: Optional[float] = None


class JobType(str, Enum):
    """对应 AIJob.JobType 枚举"""
    CANCEL = "CANCEL"
    QUERY = "QUERY"
    OTHER = "OTHER"


class AIJob(BaseModel):
    """对应 AIJob.Job record，用于规划 Agent 的结构化输出"""
    jobType: JobType = Field(  # noqa: N815
        ..., description="任务类型：退票=CANCEL，查票=QUERY，其他=OTHER"
    )
    orderNo: Optional[str] = Field(None, description="预订号/订单号")  # noqa: N815
    name: Optional[str] = Field(None, description="用户姓名")
