# -*- coding: utf-8 -*-
"""内存向量库，复刻 Spring 的 VectorStore（Java 用 pgvector，这里按"全内存化"用 InMemoryVectorStore）"""
from typing import List, Optional

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore

from app.llm.providers import get_embeddings

_store: Optional[InMemoryVectorStore] = None


def get_vector_store() -> InMemoryVectorStore:
    global _store
    if _store is None:
        _store = InMemoryVectorStore(get_embeddings())
    return _store


def add_documents(documents: List[Document]) -> None:
    get_vector_store().add_documents(documents)


def similarity_search(query: str, top_k: int = 5) -> List[Document]:
    """对应 vectorStore.similaritySearch(SearchRequest.query().topK())。"""
    return get_vector_store().similarity_search(query, k=top_k)
