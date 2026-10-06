import time
import inspect
from typing import Callable, Dict, Any, List, Optional
from pydantic import BaseModel, ValidationError
from app.models.schemas import ToolExecutionResult
from app.config import settings

class ToolRegistry:
    """Central registry and executor for Agent Tools with validation, tracing and fault simulation."""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        # Dynamic toggle for simulating tool/API failures (e.g. for testing Scenario 5)
        self.simulate_order_api_down: bool = settings.SIMULATE_ORDER_API_FAILURE

    def register(self, name: str, description: str, schema: Optional[type[BaseModel]] = None):
        """Decorator to register a tool with documentation and Pydantic validation schema."""
        def decorator(func: Callable):
            sig = inspect.signature(func)
            parameters: Dict[str, Any] = {"type": "object", "properties": {}, "required": []}

            # If Pydantic schema is provided, use its JSON schema
            if schema:
                pydantic_schema = schema.model_json_schema()
                properties = pydantic_schema.get("properties", {})
                required = pydantic_schema.get("required", [])
                parameters = {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            else:
                for param_name, param in sig.parameters.items():
                    if param_name in ("self", "cls"):
                        continue
                    param_type = "string"
                    if param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif param.annotation == list:
                        param_type = "array"

                    parameters["properties"][param_name] = {
                        "type": param_type,
                        "description": f"Argument {param_name}"
                    }
                    if param.default == inspect.Parameter.empty:
                        parameters["required"].append(param_name)

            self._tools[name] = {
                "name": name,
                "description": description,
                "func": func,
                "schema": schema,
                "parameters": parameters
            }
            return func
        return decorator

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return list(self._tools.values())

    def get_openai_function_declarations(self) -> List[Dict[str, Any]]:
        """Return tools formatted for OpenAI / Gemini function calling."""
        declarations = []
        for name, tool_info in self._tools.items():
            declarations.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool_info["description"],
                    "parameters": tool_info["parameters"]
                }
            })
        return declarations

    def execute(self, name: str, arguments: Dict[str, Any]) -> ToolExecutionResult:
        """Execute a tool with parameter validation, latency measurement, and error handling."""
        start_time = time.time()
        tool_info = self._tools.get(name)

        if not tool_info:
            latency = (time.time() - start_time) * 1000
            return ToolExecutionResult(
                tool_name=name,
                arguments=arguments,
                status="failed",
                error_message=f"Tool '{name}' is not recognized in the registry.",
                latency_ms=round(latency, 2)
            )

        # Failure simulation check for order operations
        if self.simulate_order_api_down and name in ("get_order_status", "get_order_details"):
            latency = (time.time() - start_time) * 1000
            return ToolExecutionResult(
                tool_name=name,
                arguments=arguments,
                status="failed",
                error_message="Order Service Unavailable: HTTP 503 Service Temporarily Unavailable (Gateway Timeout). The order database is temporarily unreachable.",
                latency_ms=round(latency, 2)
            )

        # Validate arguments using Pydantic schema if present
        schema = tool_info.get("schema")
        validated_args = arguments
        if schema:
            try:
                validated_model = schema(**arguments)
                validated_args = validated_model.model_dump()
            except ValidationError as ve:
                latency = (time.time() - start_time) * 1000
                error_details = "; ".join([f"{err['loc']}: {err['msg']}" for err in ve.errors()])
                return ToolExecutionResult(
                    tool_name=name,
                    arguments=arguments,
                    status="validation_error",
                    error_message=f"Validation failed for tool '{name}': {error_details}",
                    latency_ms=round(latency, 2)
                )

        try:
            func = tool_info["func"]
            result = func(**validated_args)
            latency = (time.time() - start_time) * 1000

            # Check if returned result itself is an error object
            if isinstance(result, dict) and result.get("error"):
                return ToolExecutionResult(
                    tool_name=name,
                    arguments=arguments,
                    status="failed",
                    error_message=result.get("error"),
                    data=result,
                    latency_ms=round(latency, 2)
                )

            return ToolExecutionResult(
                tool_name=name,
                arguments=arguments,
                status="success",
                data=result,
                latency_ms=round(latency, 2)
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return ToolExecutionResult(
                tool_name=name,
                arguments=arguments,
                status="failed",
                error_message=f"Execution error in '{name}': {str(e)}",
                latency_ms=round(latency, 2)
            )

tool_registry = ToolRegistry()

