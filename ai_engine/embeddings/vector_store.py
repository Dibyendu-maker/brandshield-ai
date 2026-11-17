import json
import logging
import re
from pathlib import Path
from typing import Any

from backend.core.config import settings

logger = logging.getLogger(__name__)


class VectorStoreManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.persist_dir = settings.CHROMA_PERSIST_DIR
        self._client = None
        self._cached_embedding_function = None
        self._chroma_available: bool | None = None
        self._embedding_available: bool | None = None
        self._fallback_store: dict[int, list[dict[str, Any]]] = {}
        self._load_fallback_store()
        self._initialized = True

    def _load_fallback_store(self):
        try:
            fallback_file = Path(self.persist_dir) / "deterministic_fallback_store.json"
            if fallback_file.exists():
                with open(fallback_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    self._fallback_store = {
                        int(k): v for k, v in raw.items() if str(k).isdigit()
                    }
        except Exception as e:
            logger.debug(f"[VectorStore] Could not load fallback store: {e}")
            self._fallback_store = {}

    def _save_fallback_store(self):
        try:
            fallback_dir = Path(self.persist_dir)
            fallback_dir.mkdir(parents=True, exist_ok=True)
            fallback_file = fallback_dir / "deterministic_fallback_store.json"
            with open(fallback_file, "w", encoding="utf-8") as f:
                json.dump(self._fallback_store, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug(f"[VectorStore] Could not save fallback store: {e}")

    def _init_chroma(self) -> bool:
        """Lazily initialize ChromaDB PersistentClient."""
        if self._chroma_available is False:
            return False
        if self._client is not None:
            return True

        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            self.persist_dir = settings.CHROMA_PERSIST_DIR
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._chroma_available = True
            return True
        except Exception as e:
            logger.warning(
                f"[VectorStore] ChromaDB PersistentClient unavailable, using deterministic fallback: {e}"
            )
            self._chroma_available = False
            self._client = None
            return False

    @property
    def client(self):
        self._init_chroma()
        return self._client

    @client.setter
    def client(self, value):
        self._client = value
        if value is not None:
            self._chroma_available = True

    def _init_embedding_function(self) -> bool:
        """Lazily initialize the embedding function."""
        if self._embedding_available is False:
            return False
        if self._cached_embedding_function is not None:
            return True

        try:
            from chromadb.utils import embedding_functions

            self._cached_embedding_function = (
                embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=settings.EMBEDDING_MODEL_NAME
                )
            )
            self._embedding_available = True
            return True
        except Exception as e:
            logger.warning(
                f"[VectorStore] SentenceTransformerEmbeddingFunction unavailable: {e}"
            )
            try:
                from chromadb.utils import embedding_functions

                self._cached_embedding_function = (
                    embedding_functions.DefaultEmbeddingFunction()
                )
                self._embedding_available = True
                return True
            except Exception as e2:
                logger.warning(
                    f"[VectorStore] Default embedding function unavailable: {e2}"
                )
                self._cached_embedding_function = None
                self._embedding_available = False
                return False

    @property
    def _embedding_function(self):
        self._init_embedding_function()
        return self._cached_embedding_function

    @_embedding_function.setter
    def _embedding_function(self, value):
        self._cached_embedding_function = value
        if value is not None:
            self._embedding_available = True

    def _get_collection_name(self, org_id: int) -> str:
        return f"org_{org_id}_knowledge_vault"

    def get_or_create_collection(self, org_id: int):
        if not self._init_chroma() or self._client is None:
            raise RuntimeError(
                f"[VectorStore] ChromaDB client unavailable for org {org_id}. Use fallback retrieval."
            )
        name = self._get_collection_name(org_id)
        if self._cached_embedding_function is not None:
            return self._client.get_or_create_collection(
                name=name,
                embedding_function=self._cached_embedding_function,
                metadata={"hnsw:space": "cosine"},
            )
        elif self._init_embedding_function() and self._cached_embedding_function is not None:
            return self._client.get_or_create_collection(
                name=name,
                embedding_function=self._cached_embedding_function,
                metadata={"hnsw:space": "cosine"},
            )
        else:
            return self._client.get_or_create_collection(name=name)

    def _add_to_fallback_store(
        self,
        org_id: int,
        documents: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ):
        if org_id not in self._fallback_store:
            self._fallback_store[org_id] = []

        existing_by_id = {
            item["id"]: idx for idx, item in enumerate(self._fallback_store[org_id])
        }

        for doc, meta, doc_id in zip(documents, metadatas, ids):
            record = {"id": doc_id, "text": doc, "metadata": meta}
            if doc_id in existing_by_id:
                self._fallback_store[org_id][existing_by_id[doc_id]] = record
            else:
                self._fallback_store[org_id].append(record)
                existing_by_id[doc_id] = len(self._fallback_store[org_id]) - 1

        self._save_fallback_store()

    def add_documents(
        self,
        org_id: int,
        documents: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ):
        if not documents:
            return

        # Always update the deterministic fallback store
        self._add_to_fallback_store(org_id, documents, metadatas, ids)

        # Index in ChromaDB if available
        if self._init_chroma() and self._client is not None:
            try:
                collection = self.get_or_create_collection(org_id)
                if collection is not None:
                    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
            except Exception as e:
                logger.warning(
                    f"[VectorStore] ChromaDB upsert failed, relying on deterministic fallback: {e}"
                )

    def _search_fallback(
        self, org_id: int, query: str, n_results: int = 4
    ) -> list[dict[str, Any]]:
        docs = self._fallback_store.get(org_id, [])
        if not docs or not query or not query.strip():
            return []

        query_tokens = set(re.findall(r"\w+", query.lower()))
        if not query_tokens:
            return []

        scored_docs = []
        for doc_item in docs:
            doc_text = doc_item.get("text", "")
            doc_tokens = set(re.findall(r"\w+", doc_text.lower()))
            if not doc_tokens:
                continue

            overlap = len(query_tokens & doc_tokens)
            if overlap == 0:
                continue

            # Deterministic relevance metric: Query coverage (0.7) + Jaccard similarity (0.3)
            coverage = overlap / len(query_tokens)
            jaccard = overlap / len(query_tokens | doc_tokens)
            similarity = round(0.7 * coverage + 0.3 * jaccard, 3)

            scored_docs.append((similarity, str(doc_item.get("id", "")), doc_item))

        # Sort descending by similarity, then ascending by doc_id for strict determinism
        scored_docs.sort(key=lambda x: (-x[0], x[1]))

        results = []
        for similarity, _, doc_item in scored_docs[:n_results]:
            results.append(
                {
                    "text": doc_item.get("text", ""),
                    "metadata": doc_item.get("metadata", {}),
                    "similarity": similarity,
                    "retrieval_mode": "fallback_deterministic",
                }
            )
        return results

    def search_similar(
        self,
        org_id: int,
        query: str,
        n_results: int = 4,
        force_fallback: bool = False,
    ) -> list[dict[str, Any]]:
        if not force_fallback and self._chroma_available is not False:
            try:
                if self._init_chroma() and self._client is not None:
                    name = self._get_collection_name(org_id)
                    try:
                        collection = self._client.get_collection(name=name)
                    except Exception:
                        collection = None

                    if collection is not None:
                        count = collection.count()
                        if count == 0:
                            return []

                        self._init_embedding_function()
                        if self._cached_embedding_function is not None:
                            collection = self._client.get_collection(
                                name=name,
                                embedding_function=self._cached_embedding_function,
                            )
                        limit = min(count, n_results)
                        results = collection.query(query_texts=[query], n_results=limit)

                        formatted = []
                        if results and "documents" in results and results["documents"]:
                            docs = results["documents"][0]
                            metas = (
                                results["metadatas"][0]
                                if "metadatas" in results
                                else [{}] * len(docs)
                            )
                            distances = (
                                results["distances"][0]
                                if results.get("distances")
                                else [0.0] * len(docs)
                            )

                            for doc, meta, dist in zip(docs, metas, distances):
                                similarity = round(max(0.0, 1.0 - float(dist)), 3)
                                formatted.append(
                                    {
                                        "text": doc,
                                        "metadata": meta,
                                        "similarity": similarity,
                                        "retrieval_mode": "semantic_vector",
                                    }
                                )
                            return formatted
            except Exception as e:
                logger.warning(
                    f"[VectorStore] Semantic vector query failed, using deterministic fallback: {e}"
                )

        return self._search_fallback(org_id, query, n_results=n_results)

    def delete_document(self, org_id: int, doc_id: str):
        # Remove from deterministic fallback store
        if org_id in self._fallback_store:
            self._fallback_store[org_id] = [
                item
                for item in self._fallback_store[org_id]
                if item.get("id") != doc_id
                and item.get("metadata", {}).get("doc_id") != doc_id
            ]
            self._save_fallback_store()

        # Remove from ChromaDB if client is already initialized
        if self._client is not None:
            try:
                name = self._get_collection_name(org_id)
                collection = self._client.get_collection(name=name)
                if collection is not None:
                    collection.delete(where={"doc_id": doc_id})
            except Exception:
                pass


vector_store = VectorStoreManager()
