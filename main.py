from fastapi import FastAPI, Request
import sqlite3
import json
from datetime import datetime

app = FastAPI()

conn = sqlite3.connect("madar.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT,
    chat_id TEXT,
    message_type TEXT,
    text TEXT,
    created_at TEXT,
    raw TEXT
)
""")
conn.commit()

def detect_message_type(data):
    if "text" in data:
        return "text"
    if "photo" in data:
        return "photo"
    if "video" in data:
        return "video"
    if "document" in data:
        return "document"
    return "other"

@app.get("/")
def home():
    return {"status": "ok", "project": "madar-analyzer"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    message = data.get("message", data)

    message_id = str(message.get("message_id", ""))
    chat_id = str(message.get("chat", {}).get("id", ""))
    text = message.get("text", "")

    msg_type = detect_message_type(message)

    created_at = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO messages (
            message_id,
            chat_id,
            message_type,
            text,
            created_at,
            raw
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        message_id,
        chat_id,
        msg_type,
        text,
        created_at,
        json.dumps(data)
    ))

    conn.commit()

    print("MESSAGE SAVED:", msg_type)

    return {"ok": True}
