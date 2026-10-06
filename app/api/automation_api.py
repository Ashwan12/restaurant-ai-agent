from fastapi import APIRouter
from typing import Dict, Any, List
from app.models.schemas import ComplaintWorkflowRequest, ComplaintWorkflowResult
from app.workflow.complaint_workflow import complaint_workflow
from app.db.database import db

router = APIRouter(prefix="/api/automation", tags=["Workflow Automation"])

@router.post("/complaint", summary="Trigger End-to-End Complaint Automation Workflow", response_model=ComplaintWorkflowResult)
def run_complaint_workflow(req: ComplaintWorkflowRequest) -> ComplaintWorkflowResult:
    """Executes complaint triage -> classification -> urgency -> ticket creation -> notification."""
    return complaint_workflow.execute(req)

@router.get("/events", summary="List automation workflow execution logs")
def list_workflow_events() -> List[Dict[str, Any]]:
    """Retrieve logged workflow events from database."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT workflow_id, ticket_id, customer_name, order_id, category, priority, 
               sentiment, notification_dispatched, created_at 
        FROM workflow_events 
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
