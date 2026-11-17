import base64
import hashlib
import hmac
import json
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from .models import LineAccount, ProcessedWebhookEvent


def sign(body: bytes, secret: str = "test-secret") -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def webhook_body(events: list[dict]) -> bytes:
    return json.dumps({"destination": "Ubot", "events": events}, separators=(",", ":")).encode()


def text_event(event_id: str, text: str, reply_token: str = "reply-token") -> dict:
    return {
        "type": "message",
        "webhookEventId": event_id,
        "replyToken": reply_token,
        "deliveryContext": {"isRedelivery": False},
        "source": {"type": "user", "userId": "Uuser"},
        "message": {"id": f"msg-{event_id}", "type": "text", "text": text},
    }


@override_settings(
    LINE_LOGIN_CHANNEL_ID="1234567890",
    LINE_CHANNEL_SECRET="test-secret",
    LINE_CHANNEL_ACCESS_TOKEN="test-token",
)
class HealthAndVerifyTests(TestCase):
    def test_health(self) -> None:
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "success", "message": "AI Agent backend is running"},
        )

    def test_verify_requires_id_token(self) -> None:
        response = self.client.post(
            "/api/auth/verify/",
            data=json.dumps({"displayName": "Untrusted"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "id_token is required.")

    @patch("line_integration.services.requests.post")
    def test_verify_uses_line_and_ignores_client_profile(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "iss": "https://access.line.me",
            "sub": "U123",
            "aud": "1234567890",
            "exp": 9999999999,
            "name": "Verified Name",
            "picture": "https://profile.line-scdn.net/example",
            "email": "person@example.com",
        }
        mock_post.return_value = mock_response

        response = self.client.post(
            "/api/auth/verify/",
            data=json.dumps(
                {
                    "id_token": "header.payload.signature",
                    "displayName": "Spoofed Name",
                    "userId": "Uspoof",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["user"]["userId"], "U123")
        self.assertEqual(body["user"]["displayName"], "Verified Name")
        self.assertNotIn("Spoofed", json.dumps(body))
        saved = LineAccount.objects.get(line_user_id="U123")
        self.assertEqual(saved.display_name, "Verified Name")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["data"]["client_id"], "1234567890")
        self.assertEqual(kwargs["data"]["id_token"], "header.payload.signature")

    @patch("line_integration.services.requests.post")
    def test_verify_rejects_invalid_token(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": "invalid_request",
            "error_description": "Invalid IdToken.",
        }
        mock_post.return_value = mock_response

        response = self.client.post(
            "/api/auth/verify/",
            data=json.dumps({"id_token": "not-a-token"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["message"], "Invalid IdToken.")

    @override_settings(LINE_LOGIN_CHANNEL_ID="")
    def test_verify_reports_missing_channel_id(self) -> None:
        response = self.client.post(
            "/api/auth/verify/",
            data=json.dumps({"id_token": "header.payload.signature"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 503)


@override_settings(
    LINE_LOGIN_CHANNEL_ID="1234567890",
    LINE_CHANNEL_SECRET="test-secret",
    LINE_CHANNEL_ACCESS_TOKEN="test-token",
    LIFF_ID="123-test",
    FRONTEND_URL="https://ai-agent-test.pages.dev",
)
class WebhookTests(TestCase):
    def post_webhook(self, body: bytes, signature: str | None = None):
        headers = {}
        if signature is not None:
            headers["HTTP_X_LINE_SIGNATURE"] = signature
        return self.client.post(
            "/api/line/webhook/",
            data=body,
            content_type="application/json",
            **headers,
        )

    def test_missing_signature_is_rejected(self) -> None:
        response = self.post_webhook(webhook_body([]), signature=None)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(ProcessedWebhookEvent.objects.exists())

    def test_bad_signature_is_rejected(self) -> None:
        body = webhook_body([text_event("evt-1", "Hi")])
        response = self.post_webhook(body, signature="a" * 44)
        self.assertEqual(response.status_code, 400)

    @patch("line_integration.services.requests.post")
    def test_empty_events_return_200_without_reply(self, mock_post: Mock) -> None:
        body = webhook_body([])
        response = self.post_webhook(body, sign(body))
        self.assertEqual(response.status_code, 200)
        mock_post.assert_not_called()

    @patch("line_integration.services.requests.post")
    def test_new_user_is_sent_to_the_login_page(self, mock_post: Mock) -> None:
        mock_post.return_value = Mock(status_code=200, ok=True, text="{}")
        body = webhook_body(
            [
                text_event("evt-hi", " Hi "),
                text_event("evt-other", "What can you do?", reply_token="reply-2"),
            ]
        )
        response = self.post_webhook(body, sign(body))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_post.call_count, 2)
        first = mock_post.call_args_list[0].kwargs["json"]["messages"][0]["text"]
        second = mock_post.call_args_list[1].kwargs["json"]["messages"][0]["text"]
        self.assertIn("LIFF check", first)
        self.assertIn("https://liff.line.me/123-test", first)
        self.assertEqual(first, second)
        self.assertEqual(
            mock_post.call_args_list[0].kwargs["headers"]["Authorization"],
            "Bearer test-token",
        )

    @patch("line_integration.services.requests.post")
    def test_saved_user_still_receives_the_liff_check(self, mock_post: Mock) -> None:
        mock_post.return_value = Mock(status_code=200, ok=True, text="{}")
        LineAccount.objects.create(line_user_id="Uuser", display_name="Test User")
        body = webhook_body([text_event("evt-home", "hello")])
        response = self.post_webhook(body, sign(body))
        self.assertEqual(response.status_code, 200)
        text = mock_post.call_args.kwargs["json"]["messages"][0]["text"]
        self.assertIn("https://liff.line.me/123-test", text)
        self.assertNotIn("Welcome back", text)

    @patch("line_integration.services.requests.post")
    def test_redelivery_does_not_reply_again(self, mock_post: Mock) -> None:
        mock_post.return_value = Mock(status_code=200, ok=True, text="{}")
        event = text_event("evt-same", "Hi")
        event["deliveryContext"] = {"isRedelivery": True}
        body = webhook_body([event])
        signature = sign(body)

        first = self.post_webhook(body, signature)
        second = self.post_webhook(body, signature)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(ProcessedWebhookEvent.objects.count(), 1)

    @patch("line_integration.services.requests.post")
    def test_non_text_event_is_acknowledged(self, mock_post: Mock) -> None:
        body = webhook_body(
            [
                {
                    "type": "message",
                    "webhookEventId": "evt-sticker",
                    "replyToken": "reply-sticker",
                    "message": {"id": "1", "type": "sticker", "packageId": "1", "stickerId": "1"},
                }
            ]
        )
        response = self.post_webhook(body, sign(body))
        self.assertEqual(response.status_code, 200)
        mock_post.assert_not_called()

    @patch("line_integration.services.requests.post")
    def test_failed_reply_can_be_retried(self, mock_post: Mock) -> None:
        mock_post.return_value = Mock(status_code=500, ok=False, text="error")
        body = webhook_body([text_event("evt-retry", "Hi")])
        signature = sign(body)

        failed = self.post_webhook(body, signature)
        self.assertEqual(failed.status_code, 502)
        self.assertFalse(ProcessedWebhookEvent.objects.filter(event_id="evt-retry").exists())

        mock_post.return_value = Mock(status_code=200, ok=True, text="{}")
        retried = self.post_webhook(body, signature)
        self.assertEqual(retried.status_code, 200)
        self.assertEqual(mock_post.call_count, 2)

    @override_settings(LINE_CHANNEL_SECRET="")
    def test_missing_secret_does_not_accept_unsigned_events(self) -> None:
        response = self.post_webhook(webhook_body([]), signature="anything")
        self.assertEqual(response.status_code, 503)
