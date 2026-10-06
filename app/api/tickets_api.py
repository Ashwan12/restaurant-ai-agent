from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from app.models.schemas import CreateTicketRequest, SupportTicket
from app.tools.ticket_tools import create_support_ticket
from app.db.database import db

router = APIRouter(prefix="/api/support/tickets", tags=["Support Tickets"])

@router.post("", summary="Create support ticket (Mock Operational API)")
def api_create_support_ticket(req: CreateTicketRequest) -> Dict[str, Any]:
    """Create a support ticket matching the assessment requirements."""
    res = create_support_ticket(
        customer_name=req.customer_name,
        issue_category=req.issue_category.value,
        description=req.description,
        priority=req.priority.value,
        order_id=req.order_id,
        customer_contact=req.customer_contact,
        sentiment=req.sentiment
    )
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.get("", summary="List all support tickets")
def api_list_support_tickets() -> List[Dict[str, Any]]:
    """Retrieve all tickets for review desk and UI dashboard."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ticket_id, order_id, customer_name, customer_contact, issue_category, 
               priority, description, sentiment, status, created_at, resolved_at 
        FROM support_tickets 
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
