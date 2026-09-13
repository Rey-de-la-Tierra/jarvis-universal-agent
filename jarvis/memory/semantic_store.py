"""Semantic/vector memory for knowledge indexing and retrieval."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SemanticDocument:
    """A document in the semantic memory."""
    doc_id: str
    content: str
    source: str  # URL, file path, mission ID, etc. (SourceFinder-style provenance)
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None


class SemanticStore:
    """Vector/semantic memory for knowledge indexing.
    
    Supports:
    - Document indexing with embeddings
    - Semantic search (future: via Chroma, FAISS)
    - Source provenance tracking (SourceFinder-style)
    - Knowledge base management
    """

    def __init__(self, embedding_model: Optional[Any] = None):
        """Initialize semantic store.
        
        Args:
            embedding_model: Optional embedding model (e.g., Chroma, FAISS)
        """
        self.embedding_model = embedding_model
        self._documents: Dict[str, SemanticDocument] = {}
        logger.info("Semantic store initialized (in-memory)")

    def index_document(
        self,
        doc_id: str,
        content: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Index a document in semantic memory.
        
        Args:
            doc_id: Unique document identifier
            content: Document content to index
            source: Source of the document (URL, file, mission ID, etc.)
            metadata: Optional metadata (author, date, tags, etc.)
        """
        try:
            # Compute embedding if model available
            embedding = None
            if self.embedding_model:
                embedding = self.embedding_model.embed(content)

            doc = SemanticDocument(
                doc_id=doc_id,
                content=content,
                source=source,
                embedding=embedding,
                metadata=metadata or {},
            )
            self._documents[doc_id] = doc
            logger.info(f"Document indexed: {doc_id} (source: {source})")
            return True
        except Exception as e:
            logger.error(f"Failed to index document: {e}")
            return False

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.5,
    ) -> List[SemanticDocument]:
        """Search semantic memory by query.
        
        Returns documents ranked by similarity (with provenance).
        """
        if not self.embedding_model:
            logger.warning("No embedding model configured; search unavailable")
            return []

        try:
            query_embedding = self.embedding_model.embed(query)
            # Compute similarity to all documents
            results = []
            for doc in self._documents.values():
                if doc.embedding:
                    similarity = self._cosine_similarity(query_embedding, doc.embedding)
                    if similarity >= min_similarity:
                        results.append((doc, similarity))

            # Sort by similarity (highest first)
            results.sort(key=lambda x: x[1], reverse=True)
            return [doc for doc, _ in results[:top_k]]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_document(self, doc_id: str) -> Optional[SemanticDocument]:
        """Retrieve a document by ID (with source provenance)."""
        return self._documents.get(doc_id)

    def get_by_source(self, source: str) -> List[SemanticDocument]:
        """Retrieve all documents from a specific source (SourceFinder-style)."""
        return [doc for doc in self._documents.values() if doc.source == source]

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from semantic memory."""
        if doc_id in self._documents:
            del self._documents[doc_id]
            logger.info(f"Document deleted: {doc_id}")
            return True
        return False

    def clear(self) -> None:
        """Clear all documents from semantic memory."""
        self._documents.clear()
        logger.info("Semantic memory cleared")

    def stats(self) -> Dict[str, Any]:
        """Get semantic store statistics."""
        return {
            "total_documents": len(self._documents),
            "sources": list(set(doc.source for doc in self._documents.values())),
        }

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sum(a ** 2 for a in vec_a) ** 0.5
        norm_b = sum(b ** 2 for b in vec_b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)
