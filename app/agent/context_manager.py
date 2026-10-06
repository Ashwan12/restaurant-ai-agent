import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.db.database import db

class ContextManager:
    """Manages multi-turn conversation memory with SQLite persistence."""

    def get_history(self, conversation_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Retrieve recent conversation history formatted for agent prompt."""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content FROM conversations 
            WHERE conversation_id = ? 
            ORDER BY id ASC 
            LIMIT ?
        """, (conversation_id, limit))
        rows = cursor.fetchall()
        conn.close()

        return [{"role": r["role"], "content": r["content"]} for r in rows]

    def add_message(self, conversation_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Append a message to conversation history."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        meta_json = json.dumps(metadata) if metadata else None

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO conversations (conversation_id, role, content, metadata, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (conversation_id, role, content, meta_json, now))
        conn.commit()
        conn.close()

context_manager = ContextManager()

