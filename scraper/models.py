from django.db import models


class Profile(models.Model):

    name = models.CharField(max_length=255)

    headline = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    location = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    about = models.TextField(
        blank=True,
        null=True
    )

    skills = models.TextField(
        blank=True,
        null=True
    )

    linkedin_url = models.URLField(
        unique=True
    )

    category = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name