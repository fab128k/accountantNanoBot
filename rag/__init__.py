# rag/__init__.py
# AccountantNanoBot v1.0.0 - Modulo RAG
# ============================================================================

from .models import Document, Chunk
from .chunker import TextChunker
from .vector_store import SimpleVectorStore
from .manager import KnowledgeBaseManager
from .adapters import WikiAdapter, LocalFolderAdapter

__all__ = [
    "Document",
    "Chunk",
    "TextChunker",
    "SimpleVectorStore",
    "KnowledgeBaseManager",
    "WikiAdapter",
    "LocalFolderAdapter",
]
