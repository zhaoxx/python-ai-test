# -*- coding: utf-8 -*-
"""知识库服务，复刻 service/impl/KnowledgeBaseServiceImpl.java"""
import os
import tempfile
from typing import AsyncIterator, List

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

from app.config import get_settings
from app.llm.providers import build_chat_model
from app.rag import loaders, vectorstore

RAG_PROMPT = PromptTemplate.from_template(
    "基于以下知识库内容回答用户问题。如果知识库内容无法回答问题，请明确说明。\n\n"
    "知识库内容：\n{context}\n\n"
    "用户问题：{query}\n\n"
    "请基于上述知识库内容给出准确、有用的回答："
)

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = build_chat_model("deepseek", temperature=get_settings().knowledge_temperature)
    return _model


def insert_text_content(content: str) -> int:
    """对应 insertTextContent：切分后写入向量库，返回片段数。"""
    if not content or not content.strip():
        raise ValueError("文本内容不能为空")
    docs = loaders.split_text(content)
    vectorstore.add_documents(docs)
    return len(docs)


def load_file_by_type(file_bytes: bytes, file_name: str) -> str:
    """对应 loadFileByType：落临时文件 -> 按类型读取 -> 入向量库。"""
    suffix = os.path.splitext(file_name)[1]
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        temp.write(file_bytes)
        temp.close()
        documents = loaders.load_documents(temp.name, file_name)
        if not documents:
            return f"文件 {file_name} 无法解析或不支持该格式"
        vectorstore.add_documents(documents)
        return f"成功处理文件 {file_name}，共生成 {len(documents)} 个文档片段"
    finally:
        if os.path.exists(temp.name):
            os.remove(temp.name)


def similarity_search(query: str, top_k: int = 5) -> List[Document]:
    if not query or not query.strip():
        raise ValueError("查询不能为空")
    return vectorstore.similarity_search(query, top_k)


def _build_prompt(query: str, top_k: int) -> str:
    docs = similarity_search(query, top_k)
    if not docs:
        return None
    context = "\n\n".join(d.page_content for d in docs)
    return RAG_PROMPT.format(context=context, query=query)


async def chat_with_knowledge(query: str, top_k: int = 5) -> str:
    """对应 chatWithKnowledge（非流式）。"""
    if not query or not query.strip():
        raise ValueError("查询问题不能为空")
    prompt = _build_prompt(query, top_k)
    if prompt is None:
        return "抱歉，我在知识库中没有找到相关信息来回答您的问题。"
    result = await _get_model().ainvoke(prompt)
    return result.content


async def chat_with_knowledge_stream(query: str, top_k: int = 5) -> AsyncIterator[str]:
    """对应 chatWithKnowledgeStream（流式 Flux<String>）。"""
    if not query or not query.strip():
        raise ValueError("查询问题不能为空")
    prompt = _build_prompt(query, top_k)
    if prompt is None:
        yield "抱歉，我在知识库中没有找到相关信息来回答您的问题。"
        return
    try:
        async for chunk in _get_model().astream(prompt):
            text = getattr(chunk, "content", None)
            if text:
                yield text
    except Exception as e:  # noqa: BLE001
        yield f"对话过程中发生错误: {e}"
