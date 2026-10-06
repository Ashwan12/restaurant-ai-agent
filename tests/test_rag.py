import pytest
from app.rag.knowledge_base import knowledge_base

def test_rag_cancellation_policy_retrieval():
    res = knowledge_base.query("Can I cancel my order after the restaurant accepts it?")
    assert res["grounded"] is True
    assert len(res["sources"]) > 0
    top_doc = res["sources"][0]
    assert top_doc.doc_id == "POL-CANCEL-01"
    assert "Order Cancellation Policy" in top_doc.title
    assert "kitchen preparation begins" in top_doc.snippet

def test_rag_delivery_policy_retrieval():
    res = knowledge_base.query("What is your delivery fee and how far do you deliver?")
    assert res["grounded"] is True
    assert len(res["sources"]) > 0
    top_doc = res["sources"][0]
    assert top_doc.doc_id == "POL-DELIVERY-03"
    assert "$3.99" in top_doc.snippet
    assert "8-mile radius" in top_doc.snippet

def test_rag_out_of_knowledge_fallback():
    """Demonstrate how system behaves when knowledge base does not contain the answer."""
    res = knowledge_base.query("What is the quantum mechanics formula for photon momentum?")
    assert res["grounded"] is False
    assert len(res["sources"]) == 0
    assert "could not find any documented policy" in res["message"]
