from django.contrib import admin

from .models import ProcessedWebhookEvent


@admin.register(ProcessedWebhookEvent)
class ProcessedWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "created_at")
    search_fields = ("event_id",)
    readonly_fields = ("event_id", "created_at")
