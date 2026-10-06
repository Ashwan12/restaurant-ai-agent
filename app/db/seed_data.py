import json
from datetime import datetime, timedelta
from app.db.database import db

def reset_database():
    """Drop and re-create tables, then seed fresh sample operational data."""
    db.init_db()
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM order_items")
    cursor.execute("DELETE FROM orders")
    cursor.execute("DELETE FROM support_tickets")
    cursor.execute("DELETE FROM workflow_events")
    cursor.execute("DELETE FROM audit_traces")
    cursor.execute("DELETE FROM conversations")
    conn.commit()
    conn.close()
    seed_database(force=True)

def seed_database(force: bool = False):
    """Seed sample operational data into the SQLite database."""
    db.init_db()
    conn = db.get_connection()
    cursor = conn.cursor()

    # Check if orders are already populated
    if not force:
        cursor.execute("SELECT COUNT(*) FROM orders")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return

    now = datetime.now()

    sample_orders = [
        {
            "order_id": "ORD-1001",
            "customer_name": "John Doe",
            "customer_phone": "+1-555-0101",
            "total_amount": 34.50,
            "status": "Delivered",
            "created_at": (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
            "estimated_delivery_time": "Delivered at 12:45 PM",
            "delivery_address": "742 Evergreen Terrace, Springfield",
            "driver_name": "Dave Rogers",
            "driver_phone": "+1-555-0188",
            "cancellation_reason": None,
            "items": [
                {"item_id": "ITM-01", "name": "Classic Cheeseburger", "quantity": 2, "price": 12.00, "special_instructions": "No onions"},
                {"item_id": "ITM-02", "name": "Crispy French Fries", "quantity": 1, "price": 4.50, "special_instructions": "Extra crispy"},
                {"item_id": "ITM-03", "name": "Craft Root Beer", "quantity": 2, "price": 3.00, "special_instructions": None}
            ]
        },
        {
            "order_id": "ORD-1002",
            "customer_name": "Alice Smith",
            "customer_phone": "+1-555-0102",
            "total_amount": 42.00,
            "status": "Out for Delivery",
            "created_at": (now - timedelta(minutes=40)).strftime("%Y-%m-%d %H:%M:%S"),
            "estimated_delivery_time": (now + timedelta(minutes=15)).strftime("%I:%M %p"),
            "delivery_address": "124 Conch Street, Bikini Bottom",
            "driver_name": "Mike Vance",
            "driver_phone": "+1-555-0192",
            "cancellation_reason": None,
            "items": [
                {"item_id": "ITM-04", "name": "Chicken Alfredo Pasta", "quantity": 2, "price": 18.00, "special_instructions": "Extra parmesan"},
                {"item_id": "ITM-05", "name": "Garlic Breadsticks", "quantity": 1, "price": 6.00, "special_instructions": None}
            ]
        },
        {
            "order_id": "ORD-1003",
            "customer_name": "Bob Johnson",
            "customer_phone": "+1-555-0103",
            "total_amount": 28.00,
            "status": "Preparing",
            "created_at": (now - timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S"),
            "estimated_delivery_time": (now + timedelta(minutes=30)).strftime("%I:%M %p"),
            "delivery_address": "221B Baker Street, London Area",
            "driver_name": "Unassigned (Kitchen in Progress)",
            "driver_phone": None,
            "cancellation_reason": None,
            "items": [
                {"item_id": "ITM-06", "name": "Margherita Pizza (12 inch)", "quantity": 1, "price": 18.00, "special_instructions": "Thin crust"},
                {"item_id": "ITM-07", "name": "Caesar Salad", "quantity": 1, "price": 10.00, "special_instructions": "Dressing on the side"}
            ]
        },
        {
            "order_id": "ORD-1004",
            "customer_name": "Charlie Brown",
            "customer_phone": "+1-555-0104",
            "total_amount": 19.50,
            "status": "Confirmed",
            "created_at": (now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
            "estimated_delivery_time": (now + timedelta(minutes=45)).strftime("%I:%M %p"),
            "delivery_address": "344 Pine Street, Apt 3B",
            "driver_name": None,
            "driver_phone": None,
            "cancellation_reason": None,
            "items": [
                {"item_id": "ITM-08", "name": "Spicy Buffalo Wings (10 pcs)", "quantity": 1, "price": 14.50, "special_instructions": "Ranch dip"},
                {"item_id": "ITM-09", "name": "Diet Coke Can", "quantity": 2, "price": 2.50, "special_instructions": None}
            ]
        },
        {
            # Highlighted in assessment scenario 1: "Where is my order ORD-1005?"
            "order_id": "ORD-1005",
            "customer_name": "Emma Watson",
            "customer_phone": "+1-555-0105",
            "total_amount": 56.25,
            "status": "Preparing",
            "created_at": (now - timedelta(minutes=18)).strftime("%Y-%m-%d %H:%M:%S"),
            "estimated_delivery_time": (now + timedelta(minutes=22)).strftime("%I:%M %p"),
            "delivery_address": "450 Broadway Ave, Suite 12",
            "driver_name": "Carlos Gomez (Pending pickup)",
            "driver_phone": "+1-555-0144",
            "cancellation_reason": None,
            "items": [
                {"item_id": "ITM-10", "name": "Truffle Mushroom Risotto", "quantity": 1, "price": 24.00, "special_instructions": "Gluten-free"},
                {"item_id": "ITM-11", "name": "Grilled Salmon Fillet", "quantity": 1, "price": 26.00, "special_instructions": "Medium well"},
                {"item_id": "ITM-12", "name": "Sparkling Mineral Water", "quantity": 1, "price": 6.25, "special_instructions": "With lemon slice"}
            ]
        },
        {
            "order_id": "ORD-1006",
            "customer_name": "David Miller",
            "customer_phone": "+1-555-0106",
            "total_amount": 22.00,
            "status": "Cancelled",
            "created_at": (now - timedelta(hours=1, minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
            "estimated_delivery_time": None,
            "delivery_address": "88 Riverside Drive",
            "driver_name": None,
            "driver_phone": None,
            "cancellation_reason": "Customer cancelled within 60 seconds of placing order before restaurant confirmation. Refund of $22.00 processed.",
            "items": [
                {"item_id": "ITM-13", "name": "Pepperoni Pizza (12 inch)", "quantity": 1, "price": 19.00, "special_instructions": None},
                {"item_id": "ITM-03", "name": "Craft Root Beer", "quantity": 1, "price": 3.00, "special_instructions": None}
            ]
        },
        {
            "order_id": "ORD-1007",
            "customer_name": "Sophia Taylor",
            "customer_phone": "+1-555-0107",
            "total_amount": 16.50,
            "status": "Placed",
            "created_at": (now - timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "estimated_delivery_time": (now + timedelta(minutes=40)).strftime("%I:%M %p"),
            "delivery_address": "15 Maple Court",
            "driver_name": None,
            "driver_phone": None,
            "cancellation_reason": None,
            "items": [
                {"item_id": "ITM-14", "name": "Vegetarian Pad Thai", "quantity": 1, "price": 14.00, "special_instructions": "Mild spicy"},
                {"item_id": "ITM-09", "name": "Diet Coke Can", "quantity": 1, "price": 2.50, "special_instructions": None}
            ]
        }
    ]

    for order in sample_orders:
        cursor.execute("""
            INSERT OR REPLACE INTO orders 
            (order_id, customer_name, customer_phone, total_amount, status, created_at, estimated_delivery_time, delivery_address, driver_name, driver_phone, cancellation_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order["order_id"],
            order["customer_name"],
            order["customer_phone"],
            order["total_amount"],
            order["status"],
            order["created_at"],
            order["estimated_delivery_time"],
            order["delivery_address"],
            order["driver_name"],
            order["driver_phone"],
            order["cancellation_reason"]
        ))

        for item in order["items"]:
            cursor.execute("""
                INSERT INTO order_items (order_id, item_id, name, quantity, price, special_instructions)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                order["order_id"],
                item["item_id"],
                item["name"],
                item["quantity"],
                item["price"],
                item["special_instructions"]
            ))

    # Sample Initial Support Ticket
    cursor.execute("""
        INSERT OR REPLACE INTO support_tickets
        (ticket_id, order_id, customer_name, customer_contact, issue_category, priority, description, sentiment, status, created_at, resolution_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "TCK-9001",
        "ORD-1001",
        "John Doe",
        "+1-555-0101",
        "Order",
        "Low",
        "Customer asked for nutritional information regarding the burger buns.",
        "Neutral",
        "Resolved",
        (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "Nutritional sheet sent via email."
    ))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    seed_database()
    print("Database initialized and seeded successfully.")
