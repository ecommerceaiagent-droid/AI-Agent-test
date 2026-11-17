from django.db import models


class LineAccount(models.Model):
    """A LINE user who has completed login on the website.

    The chat uses this record to decide between the login link and the homepage.
    Render's free disk is wiped when the instance is replaced, so a login can
    be forgotten after a restart until the person logs in on the website again.
    """

    line_user_id = models.CharField(max_length=128, unique=True)
    display_name = models.CharField(max_length=200, blank=True)
    picture_url = models.TextField(blank=True)
    email = models.CharField(max_length=254, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.display_name or self.line_user_id


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
