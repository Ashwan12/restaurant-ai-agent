from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
from app.db.database import db
from app.tools.order_tools import get_order_details, get_order_status
from app.tools.registry import tool_registry

router = APIRouter(prefix="/api/orders", tags=["Orders"])

@router.get("", summary="List sample operational orders")
def list_orders() -> List[Dict[str, Any]]:
    """Retrieve all sample orders for testing and UI dashboard display."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT order_id, customer_name, customer_phone, total_amount, status, 
               created_at, estimated_delivery_time, delivery_address, driver_name 
        FROM orders 
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.get("/{order_id}/status", summary="Retrieve current order status (Mock Operational API)")
def api_get_order_status(order_id: str) -> Dict[str, Any]:
    """Retrieve current order status matching the assessment requirement."""
    # Check failure simulation toggle
    if tool_registry.simulate_order_api_down:
        raise HTTPException(
            status_code=503,
            detail="Order Service Unavailable: HTTP 503 (Gateway Timeout). Database temporarily unreachable."
        )

    res = get_order_status(order_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.get("/{order_id}", summary="Retrieve order details (Mock Operational API)")
def api_get_order_details(order_id: str) -> Dict[str, Any]:
    """Retrieve full order details matching the assessment requirement."""
    if tool_registry.simulate_order_api_down:
        raise HTTPException(
            status_code=503,
            detail="Order Service Unavailable: HTTP 503 (Gateway Timeout). Database temporarily unreachable."
        )

    res = get_order_details(order_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.post("/simulate-failure", summary="Toggle order API failure simulation")
def toggle_failure_simulation(enabled: bool = Query(..., description="Set true to simulate API 503 failure, false for normal")) -> Dict[str, Any]:
    """Allows test suites and UI dashboard to toggle API downtime on the fly."""
    tool_registry.simulate_order_api_down = enabled
    return {
        "simulation_active": tool_registry.simulate_order_api_down,
        "message": f"Order API failure simulation {'ENABLED (all order queries will fail with 503)' if enabled else 'DISABLED (normal operation)'}"
    }
