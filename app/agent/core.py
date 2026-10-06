import time
import uuid
from typing import List, Dict, Any, Optional
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ToolExecutionResult,
    RAGSource
)
from app.agent.prompt_templates import SYSTEM_PROMPT
from app.agent.context_manager import context_manager
from app.agent.llm_client import llm_client
from app.tools.registry import tool_registry
from app.guardrails.security import security_guardrails
from app.observability.tracer import trace_collector
from app.observability.logger import agent_logger
from app.config import settings

class RestaurantSupportAgent:
    """Core Agent coordinating reasoning, tool execution, safety guardrails, and observability."""

    def __init__(self):
        self.max_iterations = settings.MAX_AGENT_ITERATIONS

    def process_message(self, request: ChatRequest) -> ChatResponse:
        start_time = time.time()
        conv_id = request.conversation_id or f"CONV-{uuid.uuid4().hex[:8].upper()}"
        user_msg = request.message.strip()

        # ---------------- 1. Security & Guardrails Check ----------------
        guardrail_res = security_guardrails.validate_user_input(user_msg)
        if not guardrail_res.is_safe:
            refusal_text = security_guardrails.get_security_refusal_message(guardrail_res.violation_type or "general")
            latency_ms = (time.time() - start_time) * 1000

            trace = trace_collector.record_trace(
                conversation_id=conv_id,
                user_message=user_msg,
                tools_called=[],
                rag_sources=[],
                final_response=refusal_text,
                total_latency_ms=latency_ms,
                agent_reasoning=f"Guardrail triggered: {guardrail_res.violation_type} ({guardrail_res.reason})",
                guardrail_status=f"BLOCKED: {guardrail_res.violation_type}"
            )

            # Persist in conversation memory
            context_manager.add_message(conv_id, "user", user_msg)
            context_manager.add_message(conv_id, "assistant", refusal_text, {"guardrail_blocked": True})

            return ChatResponse(
                conversation_id=conv_id,
                response=refusal_text,
                authoritative_data=None,
                tools_executed=[],
                rag_sources=[],
                guardrail_triggered=True,
                trace_id=trace.trace_id,
                execution_time_ms=round(latency_ms, 2)
            )

        # ---------------- 2. Retrieve Conversation Context ----------------
        history = context_manager.get_history(conv_id, limit=6)
        context_manager.add_message(conv_id, "user", user_msg)

        # Build prompt messages
        messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        for turn in history:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": user_msg})

        # ---------------- 3. Reasoning & Tool Calling Loop ----------------
        tools_executed: List[ToolExecutionResult] = []
        rag_sources: List[RAGSource] = []
        authoritative_data: Optional[Dict[str, Any]] = None
        final_text = ""
        agent_reasoning_notes = []

        available_tools = tool_registry.list_tools()

        for iteration in range(self.max_iterations):
            step = llm_client.call_reasoning_step(messages, available_tools)
            if step.get("reasoning"):
                agent_reasoning_notes.append(step["reasoning"])

            action = step.get("action")

            if action == "tool_call":
                tool_name = step.get("tool_name", "")
                args = step.get("arguments", {})

                # Execute tool
                tool_res = tool_registry.execute(tool_name, args)
                tools_executed.append(tool_res)

                # Capture authoritative operational data
                if tool_res.status == "success" and tool_res.data:
                    if tool_name in ("get_order_status", "get_order_details", "create_support_ticket", "cancel_order_request"):
                        authoritative_data = tool_res.data

                    # If tool was policy search, capture RAG sources
                    if tool_name == "search_restaurant_policy" and isinstance(tool_res.data, dict):
                        for s in tool_res.data.get("sources", []):
                            rag_sources.append(RAGSource(
                                doc_id=s["doc_id"],
                                title=s["title"],
                                category="Policy",
                                snippet=s["snippet"],
                                score=s["score"]
                            ))

                # Inject tool observation back into conversation loop
                messages.append({
                    "role": "tool",
                    "tool_name": tool_name,
                    "data": tool_res.data,
                    "error_message": tool_res.error_message,
                    "content": str(tool_res.data if tool_res.data else tool_res.error_message)
                })

            elif action == "respond":
                final_text = step.get("content", "")
                break
            else:
                final_text = "I have processed your request."
                break

        if not final_text and tools_executed:
            # Fallback if max iterations reached
            final_text = "I have processed your operational request. Please review the confirmed details above."

        # ---------------- 4. Secrets Masking ----------------
        final_text = security_guardrails.mask_secrets_in_output(final_text)

        # ---------------- 5. Persistence & Observability ----------------
        latency_ms = (time.time() - start_time) * 1000

        # Save assistant message in context
        context_manager.add_message(
            conv_id,
            "assistant",
            final_text,
            {"tools_count": len(tools_executed), "authoritative_data": bool(authoritative_data)}
        )

        # Record observability trace
        trace = trace_collector.record_trace(
            conversation_id=conv_id,
            user_message=user_msg,
            tools_called=tools_executed,
            rag_sources=rag_sources,
            final_response=final_text,
            total_latency_ms=latency_ms,
            agent_reasoning=" -> ".join(agent_reasoning_notes) if agent_reasoning_notes else "Direct execution",
            guardrail_status="passed"
        )

        return ChatResponse(
            conversation_id=conv_id,
            response=final_text,
            authoritative_data=authoritative_data,
            tools_executed=tools_executed,
            rag_sources=rag_sources,
            guardrail_triggered=False,
            trace_id=trace.trace_id,
            execution_time_ms=round(latency_ms, 2)
        )

restaurant_agent = RestaurantSupportAgent()

