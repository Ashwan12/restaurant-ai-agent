import pytest
from app.tools.order_tools import get_order_status, get_order_details, cancel_order_request
from app.tools.ticket_tools import create_support_ticket
from app.tools.registry import tool_registry

def test_get_order_status_valid():
    res = get_order_status("ORD-1002")
    assert res["order_id"] == "ORD-1002"
    assert res["status"] == "Out for Delivery"
    assert "Mike Vance" in res["driver_name"]

def test_get_order_status_non_existent():
    res = get_order_status("ORD-9999")
    assert "error" in res
    assert res["status"] == "not_found"

def test_get_order_details():
    res = get_order_details("ORD-1001")
    assert res["order_id"] == "ORD-1001"
    assert len(res["items"]) >= 2
    assert res["total_amount"] == 34.50

def test_tool_argument_validation_via_registry():
    # Test valid execution through registry
    success_res = tool_registry.execute("get_order_status", {"order_id": "ORD-1003"})
    assert success_res.status == "success"
    assert success_res.data["status"] == "Preparing"

    # Test validation error with illegal order format
    fail_res = tool_registry.execute("get_order_status", {"order_id": "NOT_AN_ORDER_ID"})
    assert fail_res.status == "validation_error"
    assert "Invalid order ID format" in fail_res.error_message

def test_create_support_ticket():
    res = create_support_ticket(
        customer_name="Robert Bruce",
        issue_category="Delivery",
        priority="Medium",
        description="Driver went to wrong gate at complex",
        order_id="ORD-1002"
    )
    assert res["ticket_id"].startswith("TCK-")
    assert res["status"] == "Open"
    assert res["priority"] == "Medium"

def test_cancellation_policy_enforcement():
    # Attempt to cancel ORD-1003 (which is 'Preparing') -> Should be rejected per policy
    res_rejected = cancel_order_request("ORD-1003", "Changed my mind")
    assert res_rejected["success"] is False
    assert res_rejected["policy_violation"] is True

    # Attempt to cancel ORD-1007 (which is 'Placed') -> Allowed
    res_allowed = cancel_order_request("ORD-1007", "Ordered accidentally")
    assert res_allowed["success"] is True
    assert res_allowed["status"] == "Cancelled"
