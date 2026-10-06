import re
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from app.db.database import db
from app.tools.registry import tool_registry

# Argument validation schemas
class OrderIdInput(BaseModel):
    order_id: str = Field(description="The unique order ID in format ORD-XXXX (e.g., ORD-1005)")

    @field_validator("order_id")
    @classmethod
    def validate_order_id(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r"^ORD-\d{3,6}$", v):
            raise ValueError(f"Invalid order ID format '{v}'. Valid format example: ORD-1005")
        return v

class CancelOrderInput(BaseModel):
    order_id: str = Field(description="The unique order ID to cancel, formatted ORD-XXXX")
    reason: str = Field(min_length=3, description="The customer's stated reason for cancellation")

    @field_validator("order_id")
    @classmethod
    def validate_order_id(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r"^ORD-\d{3,6}$", v):
            raise ValueError(f"Invalid order ID format '{v}'. Valid format example: ORD-1005")
        return v

@tool_registry.register(
    name="get_order_status",
    description="Retrieve the real-time operational status, ETA, and courier info for an existing customer order. Use this whenever the user asks where their order is, when it will arrive, or what state it is in.",
    schema=OrderIdInput
)
def get_order_status(order_id: str) -> Dict[str, Any]:
    """Fetch order status from operational database."""
    order_id = order_id.strip().upper()
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT order_id, customer_name, status, created_at, estimated_delivery_time, 
               driver_name, driver_phone, cancellation_reason
        FROM orders 
        WHERE order_id = ?
    """, (order_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {
            "error": f"Order '{order_id}' was not found in the restaurant operational system. Please verify the order number.",
            "status": "not_found",
            "order_id": order_id
        }

    return {
        "order_id": row["order_id"],
        "customer_name": row["customer_name"],
        "status": row["status"],
        "created_at": row["created_at"],
        "estimated_delivery_time": row["estimated_delivery_time"] or "N/A",
        "driver_name": row["driver_name"] or "Courier not yet assigned",
        "driver_phone": row["driver_phone"] or "N/A",
        "cancellation_reason": row["cancellation_reason"]
    }

@tool_registry.register(
    name="get_order_details",
    description="Retrieve complete item breakdown, total cost, delivery address, and full records for an order. Use when the user asks about specific items in their order, total price, or receipt details.",
    schema=OrderIdInput
)
def get_order_details(order_id: str) -> Dict[str, Any]:
    """Fetch full order details including line items from operational database."""
    order_id = order_id.strip().upper()
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT order_id, customer_name, customer_phone, total_amount, status, 
               created_at, estimated_delivery_time, delivery_address, driver_name, 
               driver_phone, cancellation_reason
        FROM orders 
        WHERE order_id = ?
    """, (order_id,))
    order_row = cursor.fetchone()

    if not order_row:
        conn.close()
        return {
            "error": f"Order '{order_id}' was not found in the restaurant operational system.",
            "status": "not_found",
            "order_id": order_id
        }

    cursor.execute("""
        SELECT item_id, name, quantity, price, special_instructions 
        FROM order_items 
        WHERE order_id = ?
    """, (order_id,))
    items_rows = cursor.fetchall()
    conn.close()

    items = [
        {
            "item_id": it["item_id"],
            "name": it["name"],
            "quantity": it["quantity"],
            "price": it["price"],
            "special_instructions": it["special_instructions"]
        }
        for it in items_rows
    ]

    return {
        "order_id": order_row["order_id"],
        "customer_name": order_row["customer_name"],
        "customer_phone": order_row["customer_phone"],
        "status": order_row["status"],
        "total_amount": order_row["total_amount"],
        "delivery_address": order_row["delivery_address"],
        "estimated_delivery_time": order_row["estimated_delivery_time"],
        "driver_name": order_row["driver_name"],
        "driver_phone": order_row["driver_phone"],
        "items": items,
        "items_count": len(items),
        "cancellation_reason": order_row["cancellation_reason"]
    }

@tool_registry.register(
    name="cancel_order_request",
    description="Attempt to cancel an order. Deterministically applies restaurant cancellation policy based on current order status.",
    schema=CancelOrderInput
)
def cancel_order_request(order_id: str, reason: str) -> Dict[str, Any]:
    """Execute order cancellation or reject if policy prohibits it."""
    order_id = order_id.strip().upper()
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT status, total_amount FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {"error": f"Order '{order_id}' does not exist.", "status": "not_found"}

    current_status = row["status"]

    # Deterministic policy validation:
    # 1. 'Placed' orders can be cancelled immediately with full refund.
    # 2. 'Preparing' or 'Out for Delivery' cannot be automatically cancelled without supervisor escalation.
    if current_status == "Placed":
        cursor.execute("""
            UPDATE orders 
            SET status = 'Cancelled', cancellation_reason = ? 
            WHERE order_id = ?
        """, (f"Cancelled by user: {reason}. Full refund of ${row['total_amount']:.2f} initiated.", order_id))
        conn.commit()
        conn.close()
        return {
            "success": True,
            "order_id": order_id,
            "status": "Cancelled",
            "refund_amount": row["total_amount"],
            "message": f"Order {order_id} has been successfully cancelled. A full refund of ${row['total_amount']:.2f} has been processed to your original payment method."
        }
    else:
        conn.close()
        return {
            "success": False,
            "order_id": order_id,
            "status": current_status,
            "policy_violation": True,
            "message": f"Order {order_id} is currently in '{current_status}' status. Per restaurant policy, orders cannot be directly cancelled once kitchen preparation has started or order has been dispatched. Please contact support or allow us to create a support ticket for manager review."
        }

