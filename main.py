from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok", "project": "madar-analyzer"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("NEW UPDATE:", data)
    return {"ok": True}
