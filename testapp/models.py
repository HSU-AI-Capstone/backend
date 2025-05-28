# Create your models here.
import uuid
from django.db import models

def _gen_s3_key():
    # S3 객체 키를 ‘폴더/UUID’ 형식으로 생성
    return f"lectures/{uuid.uuid4().hex}"

class Lecture(models.Model):
    title = models.CharField(max_length=255)
    professor = models.CharField(max_length=255)
    view_count = models.IntegerField(default=0)
    s3_key = models.CharField(
        max_length=255,
        unique=True,
        default=_gen_s3_key,  # ← 자동으로 고유 키 부여
        editable=False
    )
    video_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
