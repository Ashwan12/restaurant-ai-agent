import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.tools.registry import tool_registry

client = TestClient(app)

def test_api_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_api_get_orders():
    response = client.get("/api/orders")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5

def test_api_get_order_status():
    response = client.get("/api/orders/ORD-1005/status")
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == "ORD-1005"
    assert data["status"] == "Preparing"

def test_api_get_order_details():
    response = client.get("/api/orders/ORD-1005")
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == "ORD-1005"
    assert "items" in data
    assert len(data["items"]) >= 1

def test_api_create_support_ticket():
    payload = {
        "customer_name": "API Tester",
        "issue_category": "Technical",
        "priority": "Medium",
        "description": "API test ticket creation check"
    }
    response = client.post("/api/support/tickets", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ticket_id"].startswith("TCK-")

def test_api_chat_with_agent():
    payload = {
        "message": "Where is my order ORD-1005?"
    }
    response = client.post("/api/agent/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Preparing" in data["response"] or data.get("authoritative_data") is not None
    assert data["trace_id"].startswith("TRC-")

def test_api_simulate_failure_toggle():
    # Toggle failure ON
    toggle_res = client.post("/api/orders/simulate-failure?enabled=true")
    assert toggle_res.status_code == 200
    assert toggle_res.json()["simulation_active"] is True

    # Order status endpoint should return 503
    order_res = client.get("/api/orders/ORD-1005/status")
    assert order_res.status_code == 503

    # Toggle failure OFF
    client.post("/api/orders/simulate-failure?enabled=false")
    order_res2 = client.get("/api/orders/ORD-1005/status")
    assert order_res2.status_code == 200

