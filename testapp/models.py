# Create your models here.
from django.db import models


class Lecture(models.Model):
    title = models.CharField(max_length=255)
    professor = models.CharField(max_length=255)
    view_count = models.IntegerField(default=0)
    s3_key = models.CharField(max_length=512, unique=True)
    video_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
