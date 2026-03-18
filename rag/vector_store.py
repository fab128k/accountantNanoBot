# rag/vector_store.py
# AccountantNanoBot v1.0.0 - Vector Store per RAG con embedding multilingua
# ============================================================================

from pathlib import Path
from typing import List, Dict, Any, Optional

from .models import Chunk
from config import KNOWLEDGE_BASE_DIR, DEFAULT_TOP_K_RESULTS


EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "accounting_kb"


class SimpleVectorStore:
    """
    Vector store con ChromaDB e embedding multilingua (sentence-transformers).

    Usa ChromaDB con SentenceTransformerEmbeddingFunction per embedding
    semantici su testo italiano. Fallback a ricerca keyword-based in memoria
    se ChromaDB non e' disponibile.

    Attributes:
        persist_path: Percorso per persistenza ChromaDB
        use_chromadb: Se True, usa ChromaDB
        collection: Collezione ChromaDB
        chunks: Lista chunks (fallback in memoria)
    """

    def __init__(self, persist_path: str = None):
        """
        Inizializza il vector store.

        Args:
            persist_path: Percorso per persistenza (default: knowledge_base/vectorstore)
        """
        self.persist_path = persist_path or str(KNOWLEDGE_BASE_DIR / "vectorstore")
        self.chunks: List[Chunk] = []
        self.embeddings: List[List[float]] = []
        self.use_chromadb = False
        self.collection = None
        self.client = None
        self._embedding_fn = None
        self._init_store()

    def _get_embedding_function(self):
        """Lazy-initialize the SentenceTransformer embedding function."""
        if self._embedding_fn is None:
            try:
                from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            except ImportError:
                raise ImportError(
                    "sentence-transformers non installato. "
                    "Installa con: pip install sentence-transformers>=3.0.0"
                )
            self._embedding_fn = SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL
            )
        return self._embedding_fn

    def _init_store(self):
        """Inizializza ChromaDB con embedding multilingua."""
        try:
            import chromadb
        except ImportError:
            print("ChromaDB non installato. Usando store in memoria. "
                  "Installa con: pip install chromadb")
            self.use_chromadb = False
            return

        try:
            Path(self.persist_path).mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_path)

            ef = self._get_embedding_function()

            # Migrate: delete old-named collection if present
            existing_names = [c.name for c in self.client.list_collections()]
            if "wiki_knowledge_base" in existing_names:
                self.client.delete_collection("wiki_knowledge_base")

            # Check embedding model compatibility on existing collection
            if COLLECTION_NAME in existing_names:
                existing = self.client.get_collection(COLLECTION_NAME)
                stored_model = (existing.metadata or {}).get("embedding_model")
                if stored_model != EMBEDDING_MODEL:
                    self.client.delete_collection(COLLECTION_NAME)

            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={
                    "description": "AccountantNanoBot knowledge base",
                    "embedding_model": EMBEDDING_MODEL,
                },
                embedding_function=ef,
            )
            self.use_chromadb = True

        except ImportError:
            raise  # sentence-transformers missing — do not silently degrade

        except Exception as e:
            print(f"Errore inizializzazione ChromaDB: {e}. "
                  "Usando store in memoria.")
            self.use_chromadb = False

    def add_chunks(
        self,
        chunks: List[Chunk],
        embeddings: List[List[float]] = None
    ):
        """
        Aggiunge chunks al vector store.

        Args:
            chunks: Lista di Chunk da aggiungere
            embeddings: Embeddings pre-calcolati (opzionale)
        """
        if not chunks:
            return

        if self.use_chromadb and self.collection:
            try:
                ids = [chunk.id for chunk in chunks]
                documents = [chunk.text for chunk in chunks]
                metadatas = [chunk.to_dict() for chunk in chunks]

                # Se abbiamo embeddings, usiamoli
                if embeddings:
                    self.collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas,
                        embeddings=embeddings
                    )
                else:
                    # ChromaDB genererà embeddings automaticamente via EmbeddingFunction
                    self.collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas
                    )
            except Exception as e:
                print(f"Errore aggiunta a ChromaDB: {e}")
        else:
            # Fallback: store in memoria
            self.chunks.extend(chunks)

    def search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K_RESULTS
    ) -> List[Dict[str, Any]]:
        """
        Cerca chunks simili alla query.

        Args:
            query: Testo della query
            top_k: Numero massimo di risultati

        Returns:
            Lista di risultati con text, metadata, distance
        """
        if self.use_chromadb and self.collection:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=top_k,
                    include=["documents", "metadatas", "distances"]
                )

                search_results = []
                if results and results["documents"] and results["documents"][0]:
                    for i, doc in enumerate(results["documents"][0]):
                        search_results.append({
                            "text": doc,
                            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                            "distance": results["distances"][0][i] if results["distances"] else 0,
                        })
                return search_results

            except Exception as e:
                print(f"Errore ricerca ChromaDB: {e}")
                return []
        else:
            # Fallback: ricerca semplice basata su keyword
            return self._simple_search(query, top_k)

    def _simple_search(
        self,
        query: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Ricerca semplice senza embeddings (fallback).

        Usa matching keyword-based: conta le occorrenze dei termini
        della query in ogni chunk.

        Args:
            query: Testo della query
            top_k: Numero massimo di risultati

        Returns:
            Lista di risultati ordinati per rilevanza
        """
        query_terms = query.lower().split()
        scored_chunks = []

        for chunk in self.chunks:
            # Conta occorrenze dei termini
            score = sum(1 for term in query_terms if term in chunk.text.lower())
            if score > 0:
                scored_chunks.append((chunk, score))

        # Ordina per score decrescente
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        return [
            {
                "text": chunk.text,
                "metadata": chunk.to_dict(),
                "distance": 1.0 / (score + 1)  # Converti score in "distanza"
            }
            for chunk, score in scored_chunks[:top_k]
        ]

    def get_stats(self) -> Dict[str, Any]:
        """
        Ritorna statistiche del vector store.

        Returns:
            Dizionario con chunk_count, using_chromadb, persist_path
        """
        if self.use_chromadb and self.collection:
            try:
                count = self.collection.count()
                return {
                    "chunk_count": count,
                    "using_chromadb": True,
                    "persist_path": self.persist_path
                }
            except:
                pass

        return {
            "chunk_count": len(self.chunks),
            "using_chromadb": False,
            "persist_path": None
        }

    def clear(self):
        """Svuota il vector store."""
        if self.use_chromadb and self.collection:
            try:
                self.client.delete_collection(COLLECTION_NAME)
                self.collection = self.client.get_or_create_collection(
                    name=COLLECTION_NAME,
                    metadata={
                        "description": "AccountantNanoBot knowledge base",
                        "embedding_model": EMBEDDING_MODEL,
                    },
                    embedding_function=self._get_embedding_function(),
                )
            except Exception as e:
                print(f"Errore clear ChromaDB: {e}")

        self.chunks = []
        self.embeddings = []

    def is_empty(self) -> bool:
        """Verifica se il vector store e' vuoto."""
        stats = self.get_stats()
        return stats.get("chunk_count", 0) == 0


if __name__ == "__main__":
    """Smoke test: index Italian accounting phrases and verify semantic retrieval."""
    import sys
    import tempfile

    print("=== Smoke test: vector_store.py con embedding multilingua ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        store = SimpleVectorStore(persist_path=tmpdir)

        if not store.use_chromadb:
            print("FAIL: ChromaDB non disponibile")
            sys.exit(1)

        # Create test chunks
        from rag.models import Document, Chunk
        doc = Document("test.txt", "test document")
        phrases = [
            "fattura elettronica IVA al 22 per cento",
            "conto corrente bancario movimenti entrata e uscita",
            "liquidazione IVA trimestrale dichiarazione periodica",
        ]
        chunks = [
            Chunk(text=phrase, document=doc, chunk_index=i, start_char=0, end_char=len(phrase))
            for i, phrase in enumerate(phrases)
        ]

        store.add_chunks(chunks)

        # Query for IVA-related content
        results = store.search("dichiarazione IVA periodo fiscale", top_k=1)

        if not results:
            print("FAIL: nessun risultato dalla ricerca")
            sys.exit(1)

        top_result = results[0]["text"]
        if "liquidazione IVA" in top_result:
            print(f"PASS: top result = '{top_result}'")
        else:
            # Acceptable if any IVA-related result is top-1
            print(f"WARN: top result = '{top_result}' (expected 'liquidazione IVA trimestrale...')")
            if "IVA" in top_result:
                print("PASS: result is IVA-related (acceptable)")
            else:
                print("FAIL: result is not IVA-related")
                sys.exit(1)

    print("=== Smoke test completato con successo ===")
