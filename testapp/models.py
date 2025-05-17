# Create your models here.
from django.db import models


class Lecture(models.Model):
    title = models.CharField(max_length=255)
    professor = models.CharField(max_length=255)
    video_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
