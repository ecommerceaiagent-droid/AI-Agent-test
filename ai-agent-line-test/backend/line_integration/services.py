import base64
import hashlib
import hmac
import json
import logging
from typing import Any

import requests
from django.conf import settings

from .models import LineAccount, ProcessedWebhookEvent

logger = logging.getLogger(__name__)

LINE_VERIFY_URL = "https://api.line.me/oauth2/v2.1/verify"
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"
LINE_ISSUER = "https://access.line.me"
REQUEST_TIMEOUT_SECONDS = 10

def liff_check_url() -> str:
    liff_id = settings.LIFF_ID
    if liff_id:
        return f"https://liff.line.me/{liff_id}"
    return settings.FRONTEND_URL.rstrip("/")


def liff_check_message() -> str:
    lines = [
        "LIFF check",
        "",
        "Open this link in LINE. The page shows whether the LIFF app started.",
    ]
    link = liff_check_url()
    if link:
        lines.extend(["", link])
    return "\n".join(lines)


def remember_verified_user(user: dict[str, Any]) -> None:
    LineAccount.objects.update_or_create(
        line_user_id=user["userId"],
        defaults={
            "display_name": user.get("displayName") or "",
            "picture_url": user.get("pictureUrl") or "",
            "email": user.get("email") or "",
        },
    )


class LineIntegrationError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class ReplyTokenAlreadyUsed(LineIntegrationError):
    def __init__(self) -> None:
        super().__init__("Reply token was already used.", status_code=200)


def verify_id_token(id_token: str) -> dict[str, Any]:
    channel_id = settings.LINE_LOGIN_CHANNEL_ID
    if not channel_id:
        raise LineIntegrationError("LINE_LOGIN_CHANNEL_ID is not configured.", status_code=503)

    try:
        response = requests.post(
            LINE_VERIFY_URL,
            data={"id_token": id_token, "client_id": channel_id},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        logger.warning("LINE ID token verification request failed")
        raise LineIntegrationError("Could not reach LINE to verify the ID token.", status_code=502) from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise LineIntegrationError("LINE returned an unreadable verification response.", status_code=502) from exc

    if response.status_code != 200:
        description = payload.get("error_description") if isinstance(payload, dict) else None
        message = description if isinstance(description, str) and description else "Invalid ID token."
        raise LineIntegrationError(message, status_code=401)

    if not isinstance(payload, dict):
        raise LineIntegrationError("LINE returned an unexpected verification response.", status_code=502)

    audience = str(payload.get("aud", ""))
    if audience != channel_id:
        raise LineIntegrationError("ID token was not issued for this channel.", status_code=401)
    if payload.get("iss") != LINE_ISSUER:
        raise LineIntegrationError("ID token issuer is not LINE.", status_code=401)

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise LineIntegrationError("Verified token did not include a LINE user ID.", status_code=401)

    name = payload.get("name")
    picture = payload.get("picture")
    email = payload.get("email")
    expires_at = payload.get("exp")

    return {
        "userId": user_id,
        "displayName": name if isinstance(name, str) else "",
        "pictureUrl": picture if isinstance(picture, str) and picture else None,
        "email": email if isinstance(email, str) and email else None,
        "expiresAt": expires_at if isinstance(expires_at, int) else None,
    }


def is_valid_signature(body: bytes, signature: str) -> bool:
    secret = settings.LINE_CHANNEL_SECRET
    if not secret or not signature:
        return False
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode("utf-8")
    if len(signature) != len(expected):
        return False
    return hmac.compare_digest(expected, signature)


def receive_webhook(body: bytes, signature: str) -> None:
    if not settings.LINE_CHANNEL_SECRET:
        raise LineIntegrationError("LINE_CHANNEL_SECRET is not configured.", status_code=503)
    if not is_valid_signature(body, signature):
        raise LineIntegrationError("Invalid LINE webhook signature.", status_code=400)

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LineIntegrationError("Webhook body is not valid JSON.", status_code=400) from exc

    if not isinstance(payload, dict):
        raise LineIntegrationError("Webhook body must be a JSON object.", status_code=400)

    events = payload.get("events", [])
    if not isinstance(events, list):
        raise LineIntegrationError("Webhook events must be a list.", status_code=400)

    for event in events:
        if not isinstance(event, dict):
            raise LineIntegrationError("Each webhook event must be an object.", status_code=400)
        _handle_event(event)


def _handle_event(event: dict[str, Any]) -> None:
    event_id = event.get("webhookEventId")
    claimed = False
    if isinstance(event_id, str) and event_id:
        _, created = ProcessedWebhookEvent.objects.get_or_create(event_id=event_id)
        if not created:
            logger.info("Skipping redelivered LINE event %s", event_id)
            return
        claimed = True

    try:
        _reply_to_event(event)
    except ReplyTokenAlreadyUsed:
        logger.info("LINE reply token was already used for event %s", event_id or "(no id)")
    except Exception:
        if claimed and isinstance(event_id, str):
            ProcessedWebhookEvent.objects.filter(event_id=event_id).delete()
        raise


def _reply_to_event(event: dict[str, Any]) -> None:
    reply_token = event.get("replyToken")
    if not isinstance(reply_token, str) or not reply_token:
        return
    event_type = event.get("type")
    if event_type == "message":
        message = event.get("message")
        if not isinstance(message, dict) or message.get("type") != "text":
            return
        if not isinstance(message.get("text"), str):
            return
    elif event_type != "follow":
        return
    send_reply(reply_token, liff_check_message())


def send_reply(reply_token: str, text: str) -> None:
    access_token = settings.LINE_CHANNEL_ACCESS_TOKEN
    if not access_token:
        raise LineIntegrationError("LINE_CHANNEL_ACCESS_TOKEN is not configured.", status_code=503)

    try:
        response = requests.post(
            LINE_REPLY_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"replyToken": reply_token, "messages": [{"type": "text", "text": text}]},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        logger.warning("LINE reply request failed")
        raise LineIntegrationError("Could not reach LINE to send a reply.", status_code=502) from exc

    if response.status_code == 400 and "Invalid reply token" in response.text:
        raise ReplyTokenAlreadyUsed()
    if not response.ok:
        logger.warning("LINE reply API returned status %s", response.status_code)
        raise LineIntegrationError("LINE reply API rejected the message.", status_code=502)
