from fastapi import APIRouter
from typing import Dict, Any, List
from app.models.schemas import ChatRequest, ChatResponse
from app.agent.core import restaurant_agent
from app.observability.tracer import trace_collector
from app.agent.context_manager import context_manager

router = APIRouter(prefix="/api/agent", tags=["AI Agent"])

@router.post("/chat", summary="Send message to Restaurant AI Agent (Mock Operational API)", response_model=ChatResponse)
def chat_with_agent(req: ChatRequest) -> ChatResponse:
    """Send message to AI agent and receive grounded, authoritative response."""
    return restaurant_agent.process_message(req)

@router.get("/traces", summary="Retrieve recent agent observability execution traces")
def get_traces(limit: int = 25) -> List[Dict[str, Any]]:
    """Fetch live agent execution traces for the dashboard trace inspector."""
    return trace_collector.get_recent_traces(limit=limit)

@router.get("/conversations/{conversation_id}", summary="Retrieve conversation history")
def get_conversation_history(conversation_id: str) -> List[Dict[str, str]]:
    """Retrieve full history of a conversation thread."""
    return context_manager.get_history(conversation_id, limit=20)
