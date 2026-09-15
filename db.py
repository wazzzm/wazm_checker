import aiosqlite
from datetime import datetime, date
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "bot.db"


async def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                checks_today INTEGER DEFAULT 0,
                ai_today INTEGER DEFAULT 0,
                last_reset TEXT,
                is_premium INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        await db.commit()


async def get_or_create_user(user_id: int, username: str | None = None) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()

        today = date.today().isoformat()

        if row is None:
            await db.execute(
                "INSERT INTO users (user_id, username, last_reset, created_at) VALUES (?, ?, ?, ?)",
                (user_id, username, today, datetime.utcnow().isoformat())
            )
            await db.commit()
            return {
                "user_id": user_id,
                "username": username,
                "checks_today": 0,
                "ai_today": 0,
                "last_reset": today,
                "is_premium": 0
            }

        user = dict(row)
        if user["last_reset"] != today:
            await db.execute(
                "UPDATE users SET checks_today = 0, ai_today = 0, last_reset = ? WHERE user_id = ?",
                (today, user_id)
            )
            await db.commit()
            user["checks_today"] = 0
            user["ai_today"] = 0
            user["last_reset"] = today

        return user


async def increment_checks(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET checks_today = checks_today + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()


async def increment_ai(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET ai_today = ai_today + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()
