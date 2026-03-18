# rag/adapters/__init__.py
# AccountantNanoBot v1.0.0 - Modulo adapters (solo LocalFolder)
# ============================================================================

from .base import WikiAdapter
from .local_folder import LocalFolderAdapter

__all__ = [
    "WikiAdapter",
    "LocalFolderAdapter",
]
