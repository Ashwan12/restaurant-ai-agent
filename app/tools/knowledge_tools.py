from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.rag.knowledge_base import knowledge_base
from app.tools.registry import tool_registry

class PolicySearchInput(BaseModel):
    query: str = Field(min_length=3, description="Search query regarding restaurant policies, refunds, cancellation, delivery, or FAQs")

@tool_registry.register(
    name="search_restaurant_policy",
    description="Search authoritative restaurant policy documentation for rules regarding cancellation, refund policies, payment failures, delivery zones, opening hours, or allergens. Use when customer asks 'Can I cancel?', 'What is your refund policy?', 'What are your hours?', etc.",
    schema=PolicySearchInput
)
def search_restaurant_policy(query: str) -> Dict[str, Any]:
    """Retrieve grounded knowledge base articles."""
    result = knowledge_base.query(query)
    if not result["grounded"]:
        return {
            "grounded": False,
            "message": result["message"],
            "sources": []
        }

    sources_summary = [
        {"doc_id": s.doc_id, "title": s.title, "snippet": s.snippet, "score": s.score}
        for s in result["sources"]
    ]

    return {
        "grounded": True,
        "primary_title": result["primary_source"].title,
        "content": result["primary_source"].snippet,
        "sources": sources_summary
    }
