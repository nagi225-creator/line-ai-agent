"""
データベース管理
"""
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import aiosqlite

from app.models import Customer, Message, ConversationContext, PersonaType, ConversationStatus


class Database:
    """SQLiteベースのデータベース管理クラス"""
    
    def __init__(self, db_path: str = "data/database.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """データベースの初期化"""
        async with aiosqlite.connect(self.db_path) as db:
            # 顧客テーブル
            await db.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    user_id TEXT PRIMARY KEY,
                    display_name TEXT,
                    occupation TEXT,
                    interest_genre TEXT,
                    challenges TEXT,
                    goals TEXT,
                    persona TEXT DEFAULT '未特定',
                    status TEXT DEFAULT '友だち追加直後',
                    source TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            # メッセージ履歴テーブル
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (user_id) REFERENCES customers(user_id)
                )
            """)
            
            # 言及済み成功事例テーブル
            await db.execute("""
                CREATE TABLE IF NOT EXISTS mentioned_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    case_id TEXT,
                    mentioned_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES customers(user_id)
                )
            """)
            
            await db.commit()
    
    async def get_customer(self, user_id: str) -> Optional[Customer]:
        """顧客情報を取得"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM customers WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Customer(
                        user_id=row["user_id"],
                        display_name=row["display_name"],
                        occupation=row["occupation"],
                        interest_genre=json.loads(row["interest_genre"] or "[]"),
                        challenges=json.loads(row["challenges"] or "[]"),
                        goals=row["goals"],
                        persona=PersonaType(row["persona"]) if row["persona"] else PersonaType.UNKNOWN,
                        status=ConversationStatus(row["status"]) if row["status"] else ConversationStatus.INITIAL,
                        source=row["source"],
                        created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
                        updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now()
                    )
        return None
    
    async def save_customer(self, customer: Customer):
        """顧客情報を保存"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO customers 
                (user_id, display_name, occupation, interest_genre, challenges, 
                 goals, persona, status, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer.user_id,
                customer.display_name,
                customer.occupation,
                json.dumps(customer.interest_genre, ensure_ascii=False),
                json.dumps(customer.challenges, ensure_ascii=False),
                customer.goals,
                customer.persona if isinstance(customer.persona, str) else customer.persona.value,
                customer.status if isinstance(customer.status, str) else customer.status.value,
                customer.source,
                customer.created_at.isoformat(),
                datetime.now().isoformat()
            ))
            await db.commit()
    
    async def get_conversation_history(
        self, 
        user_id: str, 
        limit: int = 20
    ) -> List[Message]:
        """会話履歴を取得"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM messages 
                   WHERE user_id = ? 
                   ORDER BY timestamp DESC 
                   LIMIT ?""",
                (user_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                messages = [
                    Message(
                        id=str(row["id"]),
                        user_id=row["user_id"],
                        role=row["role"],
                        content=row["content"],
                        timestamp=datetime.fromisoformat(row["timestamp"])
                    )
                    for row in rows
                ]
                return list(reversed(messages))  # 古い順に並べ替え
    
    async def save_message(self, message: Message):
        """メッセージを保存"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO messages (user_id, role, content, timestamp)
                   VALUES (?, ?, ?, ?)""",
                (message.user_id, message.role, message.content, message.timestamp.isoformat())
            )
            await db.commit()
    
    async def get_mentioned_cases(self, user_id: str) -> List[str]:
        """言及済みの成功事例IDを取得"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT case_id FROM mentioned_cases WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
    
    async def add_mentioned_case(self, user_id: str, case_id: str):
        """言及した成功事例を記録"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO mentioned_cases (user_id, case_id, mentioned_at)
                   VALUES (?, ?, ?)""",
                (user_id, case_id, datetime.now().isoformat())
            )
            await db.commit()
    
    async def get_conversation_context(self, user_id: str) -> ConversationContext:
        """会話コンテキストを取得"""
        customer = await self.get_customer(user_id)
        if not customer:
            customer = Customer(user_id=user_id)
            await self.save_customer(customer)
        
        messages = await self.get_conversation_history(user_id)
        mentioned_cases = await self.get_mentioned_cases(user_id)
        
        return ConversationContext(
            customer=customer,
            messages=messages,
            mentioned_cases=mentioned_cases
        )


# グローバルインスタンス
db = Database()
