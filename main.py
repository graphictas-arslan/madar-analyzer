from fastapi import FastAPI, Request
import sqlite3
import json
from datetime import datetime
from fastapi.responses import HTMLResponse

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

@app.get("/stats", response_class=HTMLResponse)
def stats():
    cursor.execute("SELECT message_type FROM messages")
    rows = cursor.fetchall()

    total = len(rows)
    text = len([r for r in rows if r[0] == "text"])
    photo = len([r for r in rows if r[0] == "photo"])
    video = len([r for r in rows if r[0] == "video"])
    other = len([r for r in rows if r[0] == "other"])

    return f"""
    <html>
    <head>
        <title>Madar Analyzer</title>
        <style>
            body {{
                font-family: Arial;
                background: #0f172a;
                color: white;
                text-align: center;
                padding: 40px;
            }}
            .card {{
                display: inline-block;
                background: #1e293b;
                padding: 20px;
                margin: 10px;
                border-radius: 12px;
                width: 150px;
            }}
            .title {{
                font-size: 28px;
                margin-bottom: 30px;
            }}
            .num {{
                font-size: 32px;
                font-weight: bold;
                color: #38bdf8;
            }}
        </style>
    </head>

    <body>
        <div class="title">📊 Madar Analyzer Dashboard</div>

        <div class="card">
            <div>Total</div>
            <div class="num">{total}</div>
        </div>

        <div class="card">
            <div>Text</div>
            <div class="num">{text}</div>
        </div>

        <div class="card">
            <div>Photo</div>
            <div class="num">{photo}</div>
        </div>

        <div class="card">
            <div>Video</div>
            <div class="num">{video}</div>
        </div>

        <div class="card">
            <div>Other</div>
            <div class="num">{other}</div>
        </div>

    </body>
    </html>
    """
