from django.db import models


class ProcessedWebhookEvent(models.Model):
    """Records a LINE webhookEventId so a redelivery is not replied to twice.

    SQLite on Render's free web service is wiped when the instance is replaced.
    Deduplication lasts for the life of this database file only.
    """

    event_id = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.event_id
