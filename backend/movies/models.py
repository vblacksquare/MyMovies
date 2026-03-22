from django.db import models
from datetime import datetime


class TimestampedModel(models.Model):
    id: str

    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class Source(models.TextChoices):
    yummyanimetv = "yummyanime.tv"
    uakinogoec = "uakinogo.ec"


class SourceSession(TimestampedModel):
    cookies = models.JSONField()
    meta = models.JSONField()
    source: Source = models.CharField(
        max_length=50,
        choices=Source.choices
    )


class Translation(TimestampedModel):
    external_id = models.CharField(unique=True, max_length=100)
    title = models.TextField()
    meta = models.JSONField(default=dict)


class Movie(TimestampedModel):
    external_id = models.CharField(
        max_length=50,
        unique=True,
    )
    title = models.TextField()
    description = models.TextField(null=True, blank=True)
    poster = models.URLField(null=True, blank=True)

    fill_title = models.TextField()
    fill_description = models.TextField(null=True, blank=True)
    fill_poster = models.URLField(null=True, blank=True)

    meta = models.JSONField(default=dict)

    url = models.URLField()
    source = models.CharField(
        max_length=50,
        choices=Source.choices
    )


class MovieEpisode(TimestampedModel):
    external_id = models.CharField(unique=True, max_length=100)
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='episodes'
    )
    translation = models.ForeignKey(
        Translation,
        on_delete=models.CASCADE,
        related_name='episodes'
    )
    season = models.IntegerField()
    episode = models.IntegerField()
    meta = models.JSONField(default=dict)
    stream = models.URLField(null=True, blank=True)


class History(TimestampedModel):
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        unique=True
    )


class Socket(TimestampedModel):
    url = models.URLField()
    episode_id = models.IntegerField()
    is_active = models.BooleanField(default=True)
    headers = models.JSONField(default=dict)
    data = models.JSONField(default=dict)


class BrowserSession(TimestampedModel):
    url = models.URLField()
