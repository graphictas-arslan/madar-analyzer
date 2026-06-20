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
    raw TEXT,
    chat_type TEXT,
    chat_title TEXT
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
    cursor.execute("SELECT chat_id, message_type, raw FROM messages")
    rows = cursor.fetchall()

    channels = {}

    for chat_id, msg_type, raw in rows:

        data = json.loads(raw)
        chat = data.get("message", {}).get("chat", {})

        channel_name = chat.get("title", f"کانال {chat_id}")

        if channel_name not in channels:
            channels[channel_name] = {
                "total": 0,
                "text": 0,
                "photo": 0,
                "video": 0,
                "other": 0
            }

        channels[channel_name]["total"] += 1

        if msg_type == "text":
            channels[channel_name]["text"] += 1
        elif msg_type == "photo":
            channels[channel_name]["photo"] += 1
        elif msg_type == "video":
            channels[channel_name]["video"] += 1
        else:
            channels[channel_name]["other"] += 1

    html_cards = ""

    for name, data in channels.items():
        html_cards += f"""
        <div class="card">
            <div class="label">📢 کانال</div>
            <div style="font-size:16px; font-weight:bold; margin-bottom:10px">
                {name}
            </div>

            <div>📊 کل پیام‌ها: {data['total']}</div>
            <div>📝 متن: {data['text']}</div>
            <div>🖼 عکس: {data['photo']}</div>
            <div>🎥 ویدیو: {data['video']}</div>
            <div>📦 سایر: {data['other']}</div>
        </div>
        """

    return f"""
    <html>
    <head>
        <title>Madar Analyzer</title>
        <style>
            body {{
                margin: 0;
                font-family: Arial;
                background: linear-gradient(135deg, #0f172a, #1e293b);
                color: white;
                text-align: center;
                padding: 40px;
            }}

            h1 {{
                margin-bottom: 30px;
            }}

            .container {{
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 20px;
            }}

            .card {{
                background: rgba(255,255,255,0.08);
                padding: 20px;
                border-radius: 16px;
                width: 260px;
                text-align: right;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                direction: rtl;
            }}

            .label {{
                opacity: 0.8;
                font-size: 14px;
            }}
        </style>
    </head>

    <body>
        <h1>📊 داشبورد مادر آنالیزور</h1>

        <div class="container">
            {html_cards}
        </div>
    </body>
    </html>
    """
