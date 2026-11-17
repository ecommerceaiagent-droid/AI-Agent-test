from django.contrib import admin

from .models import LineAccount, ProcessedWebhookEvent


@admin.register(LineAccount)
class LineAccountAdmin(admin.ModelAdmin):
    list_display = ("display_name", "line_user_id", "updated_at")
    search_fields = ("display_name", "line_user_id")


@admin.register(ProcessedWebhookEvent)
class ProcessedWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "created_at")
    search_fields = ("event_id",)
    readonly_fields = ("event_id", "created_at")
