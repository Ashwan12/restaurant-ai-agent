import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re
from app.db.database import db
from app.tools.registry import tool_registry

class CreateTicketInput(BaseModel):
    order_id: Optional[str] = Field(default=None, description="Optional associated order ID (e.g. ORD-1005)")
    customer_name: str = Field(min_length=2, max_length=100, description="Full name of customer")
    customer_contact: Optional[str] = Field(default=None, description="Customer phone number or email")
    issue_category: str = Field(description="Category: Payment, Order, Delivery, Refund, or Technical")
    priority: str = Field(default="Medium", description="Priority level: Low, Medium, or High")
    description: str = Field(min_length=5, max_length=1000, description="Detailed explanation of the support issue or complaint")
    sentiment: Optional[str] = Field(default="Neutral", description="Assessed customer sentiment")

    @field_validator("order_id")
    @classmethod
    def validate_order_id(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip().upper()
            if not re.match(r"^ORD-\d{3,6}$", v):
                raise ValueError("Order ID must follow ORD-XXXX format")
            return v
        return v

    @field_validator("issue_category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        valid = ["Payment", "Order", "Delivery", "Refund", "Technical"]
        v_title = v.strip().capitalize()
        for cat in valid:
            if cat.lower() == v.strip().lower():
                return cat
        raise ValueError(f"Invalid category '{v}'. Allowed: {', '.join(valid)}")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        valid = ["Low", "Medium", "High"]
        for p in valid:
            if p.lower() == v.strip().lower():
                return p
        raise ValueError(f"Invalid priority '{v}'. Allowed: {', '.join(valid)}")

@tool_registry.register(
    name="create_support_ticket",
    description="Create an official customer support ticket for unresolved issues, payment disputes, refunds, delayed orders, or complaints. Returns ticket ID and confirmation.",
    schema=CreateTicketInput
)
def create_support_ticket(
    customer_name: str,
    issue_category: str,
    description: str,
    priority: str = "Medium",
    order_id: Optional[str] = None,
    customer_contact: Optional[str] = None,
    sentiment: Optional[str] = "Neutral"
) -> Dict[str, Any]:
    """Persist a new support ticket in the database."""
    conn = db.get_connection()
    cursor = conn.cursor()

    # Generate next sequential ticket ID
    cursor.execute("SELECT COUNT(*) FROM support_tickets")
    count = cursor.fetchone()[0] + 1
    ticket_id = f"TCK-{9000 + count}"

    now = datetime.now()
    created_at = now.strftime("%Y-%m-%d %H:%M:%S")

    # Verify order_id existence if provided
    if order_id:
        order_id = order_id.strip().upper()
        cursor.execute("SELECT order_id FROM orders WHERE order_id = ?", (order_id,))
        if not cursor.fetchone():
            conn.close()
            return {
                "error": f"Cannot link ticket to unknown order ID '{order_id}'. Please verify the order number.",
                "status": "validation_error"
            }

    cursor.execute("""
        INSERT INTO support_tickets 
        (ticket_id, order_id, customer_name, customer_contact, issue_category, priority, description, sentiment, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticket_id,
        order_id,
        customer_name,
        customer_contact,
        issue_category,
        priority,
        description,
        sentiment,
        "Open",
        created_at
    ))
    conn.commit()
    conn.close()

    # Estimated resolution SLA based on priority
    sla_map = {
        "High": "1 hour (Emergency escalation to supervisor)",
        "Medium": "4 hours",
        "Low": "24 hours"
    }

    return {
        "ticket_id": ticket_id,
        "order_id": order_id,
        "customer_name": customer_name,
        "issue_category": issue_category,
        "priority": priority,
        "status": "Open",
        "created_at": created_at,
        "estimated_sla": sla_map.get(priority, "4 hours"),
        "confirmation_message": f"Support Ticket #{ticket_id} has been logged under priority '{priority}'. Our support team will review it within {sla_map.get(priority, '4 hours')}."
    }
