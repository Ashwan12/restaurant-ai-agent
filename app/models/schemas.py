from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import re

# ----------------- Orders -----------------
class OrderStatusEnum(str, Enum):
    PLACED = "Placed"
    CONFIRMED = "Confirmed"
    PREPARING = "Preparing"
    OUT_FOR_DELIVERY = "Out for Delivery"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"

class OrderItem(BaseModel):
    item_id: str
    name: str
    quantity: int = Field(gt=0)
    price: float = Field(ge=0.0)
    special_instructions: Optional[str] = None

class OrderDetails(BaseModel):
    order_id: str
    customer_name: str
    customer_phone: Optional[str] = None
    items: List[OrderItem]
    total_amount: float
    status: OrderStatusEnum
    created_at: str
    estimated_delivery_time: Optional[str] = None
    delivery_address: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    cancellation_reason: Optional[str] = None

    @field_validator("order_id")
    @classmethod
    def validate_order_id_format(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r"^ORD-\d{3,6}$", v):
            raise ValueError("Order ID must follow the format ORD-XXXX (e.g., ORD-1005)")
        return v

class OrderStatusResponse(BaseModel):
    order_id: str
    status: OrderStatusEnum
    updated_at: str
    estimated_delivery_time: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    details_summary: Optional[str] = None

# ----------------- Support Tickets -----------------
class IssueCategory(str, Enum):
    PAYMENT = "Payment"
    ORDER = "Order"
    DELIVERY = "Delivery"
    REFUND = "Refund"
    TECHNICAL = "Technical"

class TicketPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class TicketStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    ESCALATED = "Escalated"

class CreateTicketRequest(BaseModel):
    order_id: Optional[str] = None
    customer_name: str = Field(min_length=2, max_length=100)
    customer_contact: Optional[str] = None
    issue_category: IssueCategory
    priority: TicketPriority = TicketPriority.MEDIUM
    description: str = Field(min_length=5, max_length=1000)
    sentiment: Optional[str] = "Neutral"

    @field_validator("order_id")
    @classmethod
    def validate_optional_order_id(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip().upper()
            if not re.match(r"^ORD-\d{3,6}$", v):
                raise ValueError("Order ID must follow the format ORD-XXXX (e.g., ORD-1005)")
            return v
        return v

class SupportTicket(BaseModel):
    ticket_id: str
    order_id: Optional[str] = None
    customer_name: str
    customer_contact: Optional[str] = None
    issue_category: IssueCategory
    priority: TicketPriority
    description: str
    sentiment: Optional[str] = "Neutral"
    status: TicketStatus = TicketStatus.OPEN
    created_at: str
    resolved_at: Optional[str] = None
    resolution_notes: Optional[str] = None

# ----------------- Automation Workflow -----------------
class ComplaintAnalysis(BaseModel):
    issue_category: IssueCategory
    priority: TicketPriority
    sentiment: str = Field(description="Customer sentiment (e.g., Frustrated, Angry, Neutral, Polite)")
    urgency_reasoning: str = Field(description="Explanation of why this priority level was assigned")
    summary: str = Field(description="Concise summary of the customer's issue")
    requires_human_escalation: bool = False

class ComplaintWorkflowRequest(BaseModel):
    customer_name: str
    message: str
    order_id: Optional[str] = None
    customer_contact: Optional[str] = None

class ComplaintWorkflowResult(BaseModel):
    workflow_id: str
    ticket_id: str
    customer_name: str
    order_id: Optional[str] = None
    analysis: ComplaintAnalysis
    notification_dispatched: bool
    notification_channel: str
    status: str
    created_at: str

# ----------------- Guardrails -----------------
class GuardrailCheckResult(BaseModel):
    is_safe: bool
    violation_type: Optional[str] = None
    reason: Optional[str] = None
    sanitized_input: Optional[str] = None

# ----------------- Tools & RAG -----------------
class ToolExecutionResult(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    status: str  # 'success', 'failed', 'timeout', 'validation_error'
    data: Optional[Any] = None
    error_message: Optional[str] = None
    latency_ms: float = 0.0

class RAGSource(BaseModel):
    doc_id: str
    title: str
    category: str
    snippet: str
    score: float

# ----------------- Chat & Observability -----------------
class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: Optional[str] = None
    user_id: Optional[str] = "guest_customer"
    context_order_id: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    authoritative_data: Optional[Dict[str, Any]] = None
    tools_executed: List[ToolExecutionResult] = []
    rag_sources: List[RAGSource] = []
    guardrail_triggered: bool = False
    trace_id: str
    execution_time_ms: float

class AgentTrace(BaseModel):
    trace_id: str
    conversation_id: str
    timestamp: str
    user_message: str
    agent_reasoning: Optional[str] = None
    tools_called: List[ToolExecutionResult] = []
    rag_sources: List[RAGSource] = []
    guardrail_status: str = "passed"
    final_response: str
    total_latency_ms: float
    error: Optional[str] = None

