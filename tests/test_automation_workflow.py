import pytest
from app.workflow.complaint_workflow import complaint_workflow
from app.models.schemas import ComplaintWorkflowRequest, IssueCategory, TicketPriority

def test_workflow_payment_complaint():
    req = ComplaintWorkflowRequest(
        customer_name="Samantha Clark",
        order_id="ORD-1004",
        message="My bank card was charged twice but the order checkout showed an error!"
    )
    res = complaint_workflow.execute(req)

    assert res.status == "completed"
    assert res.analysis.issue_category == IssueCategory.PAYMENT
    assert res.analysis.priority == TicketPriority.HIGH
    assert res.analysis.requires_human_escalation is True
    assert res.notification_dispatched is True
    assert res.ticket_id.startswith("TCK-")

def test_workflow_delivery_delay():
    req = ComplaintWorkflowRequest(
        customer_name="Marcus Vance",
        order_id="ORD-1002",
        message="The driver has been stuck for an hour and the food will be cold."
    )
    res = complaint_workflow.execute(req)

    assert res.analysis.issue_category == IssueCategory.DELIVERY
    assert res.ticket_id.startswith("TCK-")

def test_workflow_idempotency_prevents_duplicate_tickets():
    """Verify that retrying identical complaint does not create duplicate support tickets."""
    req = ComplaintWorkflowRequest(
        customer_name="Idempotency Tester",
        order_id="ORD-1005",
        message="Exact duplicate complaint message to verify idempotency prevention."
    )
    # First execution
    res1 = complaint_workflow.execute(req)
    assert res1.status == "completed"
    first_ticket_id = res1.ticket_id

    # Second execution (e.g. agent retry)
    res2 = complaint_workflow.execute(req)
    assert res2.status == "idempotent_duplicate_prevented"
    assert res2.ticket_id == first_ticket_id, "Ticket ID must match existing ticket instead of creating a duplicate."

