from fastapi import FastAPI, Request
from dotenv import load_dotenv
import os, httpx
import asyncio

load_dotenv(override=True)

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

@app.get("/")
async def hello():
    return {"response": "Hello Whatsapp API"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    if params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(params.get("hub.challenge"))
    return {"status": "Unauthorized"}, 403

@app.post("/webhook")
async def receive_message(req: Request):
    data = await req.json()
    print("Incoming:", data)
    try:
        message = data['entry'][0]['changes'][0]['value']['messages'][0]
        sender = message['from']
        sender = "52" + sender[3:]
        print("SENDER:", sender)
        message_id = message['id']

        await mark_as_read(message_id)  # 👈 this line

        reply = "Hi! 👋 This is a FastAPI WhatsApp bot! Yeah 😎!"
        await asyncio.sleep(5)  # optional: simulate delay
        await send_whatsapp_message(sender, reply)
    except Exception as e:
        print("Error:", e)
    return {"status": "received"}

async def send_whatsapp_message(to: str, message: str):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    json = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers=headers, json=json)
        print("Response:", r.status_code, r.text)


async def mark_as_read(message_id: str):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
        "typing_indicator": {
            "type": "text"
        },
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        print("Marked as read:", response.status_code, response.text)