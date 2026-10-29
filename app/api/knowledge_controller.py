# -*- coding: utf-8 -*-
"""知识库接口，复刻 controller/KnowledgeBaseController.java
路径与语义保持一致：/api/v1/knowledge-base/*
"""
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import PlainTextResponse, StreamingResponse

from app.rag import knowledge as kb

router = APIRouter(prefix="/api/v1/knowledge-base", tags=["knowledge-base"])


@router.get("/insert-text", response_class=PlainTextResponse)
async def insert_text_content(content: str = Query(...)):
    if not content or not content.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "文本内容是必需的")
    try:
        count = kb.insert_text_content(content)
        return f"文本内容已成功插入，生成 {count} 个片段"
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"插入文本内容失败: {e}")


@router.post("/upload-file", response_class=PlainTextResponse)
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "文件为空")
    try:
        return kb.load_file_by_type(content, file.filename or "upload.tmp")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"文件上传失败: {e}")


@router.get("/search")
async def search(query: str = Query(...), topK: int = Query(5, ge=1)):  # noqa: N803
    if not query or not query.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "查询内容是必需的")
    try:
        docs = kb.similarity_search(query, topK)
        return [
            {"content": d.page_content, "metadata": d.metadata} for d in docs
        ]
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"相似性搜索出错: {e}")


@router.get("/chat", response_class=PlainTextResponse)
async def chat(query: str = Query(...), topK: int = Query(5, ge=1)):  # noqa: N803
    if not query or not query.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "查询问题是必需的")
    try:
        return await kb.chat_with_knowledge(query, topK)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"对话过程中发生错误: {e}")


@router.get("/chat-stream")
async def chat_stream(query: str = Query(...), topK: int = Query(5, ge=1)):  # noqa: N803
    if not query or not query.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "查询问题是必需的")
    return StreamingResponse(
        kb.chat_with_knowledge_stream(query, topK),
        media_type="text/event-stream",
    )
