import sqlite3
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.config import settings

class Database:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_PATH

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Orders Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                customer_name TEXT NOT NULL,
                customer_phone TEXT,
                total_amount REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                estimated_delivery_time TEXT,
                delivery_address TEXT,
                driver_name TEXT,
                driver_phone TEXT,
                cancellation_reason TEXT
            )
        """)

        # Order Items Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                special_instructions TEXT,
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            )
        """)

        # Support Tickets Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                ticket_id TEXT PRIMARY KEY,
                order_id TEXT,
                customer_name TEXT NOT NULL,
                customer_contact TEXT,
                issue_category TEXT NOT NULL,
                priority TEXT NOT NULL,
                description TEXT NOT NULL,
                sentiment TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                resolution_notes TEXT,
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            )
        """)

        # Conversation History Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # Workflow Automation Log Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_events (
                workflow_id TEXT PRIMARY KEY,
                ticket_id TEXT,
                customer_name TEXT,
                order_id TEXT,
                category TEXT,
                priority TEXT,
                sentiment TEXT,
                notification_dispatched INTEGER,
                raw_payload TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # Observability / Audit Trace Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_traces (
                trace_id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                user_message TEXT,
                tools_called TEXT,
                rag_sources TEXT,
                guardrail_status TEXT,
                final_response TEXT,
                latency_ms REAL,
                error TEXT
            )
        """)

        conn.commit()
        conn.close()

db = Database()
