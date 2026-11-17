import logging

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import LineIntegrationError, receive_webhook, verify_id_token

logger = logging.getLogger(__name__)

MAX_ID_TOKEN_LENGTH = 16384


class HealthView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "status": "success",
                "message": "AI Agent backend is running",
            }
        )


class LineVerifyView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get("id_token") if isinstance(request.data, dict) else None
        if not isinstance(id_token, str) or not id_token.strip():
            return Response({"status": "error", "message": "id_token is required."}, status=400)
        if len(id_token) > MAX_ID_TOKEN_LENGTH:
            return Response({"status": "error", "message": "id_token is too long."}, status=400)

        try:
            user = verify_id_token(id_token.strip())
        except LineIntegrationError as exc:
            logger.info("LINE ID token verification failed with status %s", exc.status_code)
            return Response({"status": "error", "message": str(exc)}, status=exc.status_code)

        return Response({"status": "success", "user": user})


class LineWebhookView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request):
        signature = request.headers.get("X-Line-Signature", "")
        try:
            receive_webhook(request.body, signature)
        except LineIntegrationError as exc:
            logger.info("LINE webhook rejected with status %s", exc.status_code)
            return Response({"status": "error", "message": str(exc)}, status=exc.status_code)

        return Response({"status": "success"}, status=200)
