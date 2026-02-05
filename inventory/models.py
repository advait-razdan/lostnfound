from django.conf import settings
from django.db import models


class Item(models.Model):
    class Status(models.TextChoices):
        FOUND = "FOUND", "Found"
        CLAIMED = "CLAIMED", "Claimed"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    location_found = models.CharField(max_length=255, blank=True)
    date_found = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.FOUND,
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_found", "-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["date_found"]),
        ]

    def __str__(self) -> str:
        return self.title


class ItemImage(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="item_images/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Image for {self.item_id}"


