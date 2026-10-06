from typing import List, Dict, Any, Optional
from app.rag.vector_store import vector_store
from app.models.schemas import RAGSource
from app.config import settings

class KnowledgeBase:
    """High-level Knowledge Base for RAG queries and grounded retrieval."""

    def __init__(self):
        self.store = vector_store

    def query(self, user_question: str, top_k: Optional[int] = None, threshold: Optional[float] = None) -> Dict[str, Any]:
        """Query the knowledge base and return grounded sources and grounding status."""
        k = top_k or settings.RAG_TOP_K
        thresh = threshold or settings.RAG_SIMILARITY_THRESHOLD

        sources: List[RAGSource] = self.store.search(user_question, top_k=k, threshold=thresh)

        if not sources:
            return {
                "grounded": False,
                "sources": [],
                "message": (
                    "I checked our restaurant policies and operating documentation, but I could not find "
                    "any documented policy or answer regarding this specific topic. To assist you further, "
                    "I can connect you with our restaurant manager or open a support ticket."
                ),
                "top_score": 0.0
            }

        # Build grounded context string
        context_snippets = []
        for src in sources:
            context_snippets.append(f"[{src.doc_id}] {src.title}:\n{src.snippet}")

        return {
            "grounded": True,
            "sources": sources,
            "context_text": "\n\n".join(context_snippets),
            "top_score": sources[0].score,
            "primary_source": sources[0]
        }

knowledge_base = KnowledgeBase()

