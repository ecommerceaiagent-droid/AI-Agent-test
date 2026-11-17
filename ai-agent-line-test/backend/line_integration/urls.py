from django.urls import path

from .views import HealthView, LineVerifyView, LineWebhookView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("auth/verify/", LineVerifyView.as_view(), name="line-verify"),
    path("line/webhook/", LineWebhookView.as_view(), name="line-webhook"),
]
