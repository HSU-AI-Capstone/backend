from PyPDF2 import PdfReader
from rest_framework import serializers

from .models import Lecture


class LectureUploadSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=2048)
    professor = serializers.CharField(max_length=255)
    file = serializers.FileField()

    def validate_file(self, value):
        if value.content_type != "application/pdf" or not value.name.endswith(".pdf"):
            raise serializers.ValidationError("PDF 파일만 업로드할 수 있습니다.")

        try:
            value.seek(0)
            PdfReader(value)
        except Exception:
            raise serializers.ValidationError("손상된 PDF 파일입니다.")
        finally:
            value.seek(0)
        return value


class LectureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lecture
        fields = ["id", "title", "professor", "view_count", "video_url", "created_at"]


class LectureDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lecture
        fields = ["id", "title", "professor", "view_count", "video_url", "created_at"]
