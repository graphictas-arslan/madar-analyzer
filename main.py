from fastapi import FastAPI, Request
import sqlite3
import json

app = FastAPI()

# دیتابیس ساده
conn = sqlite3.connect("madar.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw TEXT
)
""")
conn.commit()

@app.get("/")
def home():
    return {"status": "ok", "project": "madar-analyzer"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    # ذخیره پیام خام
    cursor.execute(
        "INSERT INTO messages (raw) VALUES (?)",
        (json.dumps(data),)
    )
    conn.commit()

    print("SAVED MESSAGE")

    return {"ok": True}
