import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.models.schemas import AgentTrace, ToolExecutionResult, RAGSource
from app.db.database import db
from app.observability.logger import agent_logger

class TraceCollector:
    """Observability trace collector recording all agent decisions, tool steps, and latencies."""

    def __init__(self):
        self._memory_traces: List[AgentTrace] = []

    def record_trace(
        self,
        conversation_id: str,
        user_message: str,
        tools_called: List[ToolExecutionResult],
        rag_sources: List[RAGSource],
        final_response: str,
        total_latency_ms: float,
        agent_reasoning: Optional[str] = None,
        guardrail_status: str = "passed",
        error: Optional[str] = None
    ) -> AgentTrace:
        trace_id = f"TRC-{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now().isoformat()

        trace = AgentTrace(
            trace_id=trace_id,
            conversation_id=conversation_id,
            timestamp=timestamp,
            user_message=user_message,
            agent_reasoning=agent_reasoning,
            tools_called=tools_called,
            rag_sources=rag_sources,
            guardrail_status=guardrail_status,
            final_response=final_response,
            total_latency_ms=round(total_latency_ms, 2),
            error=error
        )

        # Store in-memory (limited to last 100)
        self._memory_traces.insert(0, trace)
        if len(self._memory_traces) > 100:
            self._memory_traces.pop()

        # Persist into SQLite
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_traces 
                (trace_id, conversation_id, timestamp, user_message, tools_called, rag_sources, guardrail_status, final_response, latency_ms, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trace_id,
                conversation_id,
                timestamp,
                user_message,
                json.dumps([t.model_dump() for t in tools_called]),
                json.dumps([s.model_dump() for s in rag_sources]),
                guardrail_status,
                final_response,
                round(total_latency_ms, 2),
                error
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            agent_logger.error(f"Failed to persist trace to DB: {e}")

        # Structured log
        agent_logger.info(
            f"Trace recorded: {trace_id} | Conv: {conversation_id} | Tools: {len(tools_called)} | Latency: {round(total_latency_ms, 2)}ms | Guardrail: {guardrail_status}"
        )

        return trace

    def get_recent_traces(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch latest traces from database or memory."""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT trace_id, conversation_id, timestamp, user_message, tools_called, 
                       rag_sources, guardrail_status, final_response, latency_ms, error 
                FROM audit_traces 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            conn.close()

            traces = []
            for r in rows:
                traces.append({
                    "trace_id": r["trace_id"],
                    "conversation_id": r["conversation_id"],
                    "timestamp": r["timestamp"],
                    "user_message": r["user_message"],
                    "tools_called": json.loads(r["tools_called"]) if r["tools_called"] else [],
                    "rag_sources": json.loads(r["rag_sources"]) if r["rag_sources"] else [],
                    "guardrail_status": r["guardrail_status"],
                    "final_response": r["final_response"],
                    "latency_ms": r["latency_ms"],
                    "error": r["error"]
                })
            return traces
        except Exception as e:
            agent_logger.warning(f"Failed reading traces from DB, using memory: {e}")
            return [t.model_dump() for t in self._memory_traces[:limit]]

trace_collector = TraceCollector()

