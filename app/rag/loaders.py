# -*- coding: utf-8 -*-
"""文档加载与切分，复刻 KnowledgeBaseServiceImpl 里的 PDF/Tika 读取 + TokenTextSplitter"""
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def _text_splitter() -> RecursiveCharacterTextSplitter:
    # 对应 new TokenTextSplitter()
    return RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)


def split_text(content: str) -> List[Document]:
    """对应 insertTextContent 里的 TokenTextSplitter().apply(List.of(document))。"""
    docs = [Document(page_content=content)]
    return _text_splitter().split_documents(docs)


def load_documents(file_path: str, file_name: str) -> List[Document]:
    """按扩展名选择读取器：PDF 用 PyPDFLoader，其它用文本读取（对应 Tika）。"""
    if file_name.lower().endswith(".pdf"):
        from langchain_community.document_loaders import PyPDFLoader

        return PyPDFLoader(file_path).load()

    # Tika 兜底：按纯文本读取（txt/md/csv 等）
    from langchain_community.document_loaders import TextLoader

    try:
        return TextLoader(file_path, encoding="utf-8").load()
    except UnicodeDecodeError:
        # 二进制非 PDF 文件无法可靠解析，返回空并让上层提示
        return []
