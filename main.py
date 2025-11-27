from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import httpx
import asyncio
import logging
from typing import Any

load_dotenv(override=True)

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whatsapp_service")

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

if not all([VERIFY_TOKEN, WHATSAPP_TOKEN, PHONE_NUMBER_ID]):
    logger.error("Missing required environment variables.")
    raise RuntimeError(
        "Missing required environment variables: VERIFY_TOKEN, WHATSAPP_TOKEN, PHONE_NUMBER_ID"
    )


@app.get("/")
async def hello() -> dict[str, str]:
    """Root endpoint for health check."""
    return {"response": "Hello Whatsapp API"}


@app.get("/webhook")
async def verify_webhook(request: Request) -> Any:
    """Verify webhook for WhatsApp Cloud API."""
    params = dict(request.query_params)
    if params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(params.get("hub.challenge"))
    return JSONResponse(
        content={"status": "Unauthorized"}, status_code=status.HTTP_403_FORBIDDEN
    )


@app.post("/webhook")
async def receive_message(req: Request) -> JSONResponse:
    """Receive and respond to WhatsApp messages."""
    try:
        data = await req.json()
        logger.info(f"Incoming: {data}")
        message = data["entry"][0]["changes"][0]["value"].get("messages", [{}])[0]
        sender = message.get("from")
        if not sender:
            logger.warning("No sender found in message.")
            return JSONResponse(
                content={"status": "No sender found"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        sender = "52" + sender[3:]
        logger.info(f"SENDER: {sender}")
        message_id = message.get("id")
        if message_id:
            await mark_as_read(message_id)
        reply = "Hi! 👋 This is a FastAPI WhatsApp bot! Yeaaaah 😎!"
        await asyncio.sleep(1)  # optional: simulate delay
        await send_whatsapp_message(sender, reply)
        return JSONResponse(
            content={"status": "received"}, status_code=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        return JSONResponse(
            content={"status": "error", "detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


async def send_whatsapp_message(to: str, message: str) -> None:
    """Send a WhatsApp message using the Cloud API."""
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    json = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers=headers, json=json)
        logger.info(f"WhatsApp API response: {r.status_code} {r.text}")


async def mark_as_read(message_id: str) -> None:
    """Mark a WhatsApp message as read using the Cloud API."""
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
        "typing_indicator": {"type": "text"},
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        logger.info(f"Marked as read: {response.status_code} {response.text}")
