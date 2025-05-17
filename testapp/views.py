import os
import tempfile
import uuid

from PyPDF2 import PdfReader
from django.http import HttpResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Lecture
from .s3_upload import upload_file_to_s3
from .serializers import LectureSerializer, LectureDetailSerializer
from .utils import generate_lecture_video


def index(request):
    return HttpResponse("설정이 완료되었습니다.")


class UploadLectureView(APIView):
    parser_classes = [MultiPartParser]

    @swagger_auto_schema(
        operation_summary="강의 업로드",
        operation_description="PDF 파일을 업로드하여 강의 영상을 생성하고, S3에 업로드한 뒤 Lecture 객체를 생성합니다.",
        manual_parameters=[
            openapi.Parameter(
                "title",
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="강의 제목",
            ),
            openapi.Parameter(
                "professor",
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="교수 이름",
            ),
            openapi.Parameter(
                "file",
                openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="PDF 파일",
            ),
        ],
        responses={
            201: openapi.Response(
                "성공",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "lecture_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "video_url": openapi.Schema(
                            type=openapi.TYPE_STRING, format="url"
                        ),
                    },
                ),
            ),
            400: "잘못된 요청",
        },
    )
    def post(self, request, *args, **kwargs):
        pdf_file = request.FILES.get("file")
        title = request.data.get("title")
        professor = request.data.get("professor")

        if not pdf_file:
            return Response({"error": "PDF 파일이 필요합니다."}, status=400)

        if pdf_file.content_type != "application/pdf" or not pdf_file.name.endswith(
            ".pdf"
        ):
            return Response({"error": "PDF 파일만 업로드할 수 있습니다."}, status=400)

        try:
            pdf_file.seek(0)
            PdfReader(pdf_file)
        except Exception:
            return Response({"error": "손상된 PDF 파일입니다."}, status=400)

        pdf_file.seek(0)

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, pdf_file.name)
            with open(pdf_path, "wb") as f:
                for chunk in pdf_file.chunks():
                    f.write(chunk)

            video_path = generate_lecture_video(pdf_path)
            video_filename = f"{uuid.uuid4().hex}.mp4"
            video_url = upload_file_to_s3(video_path, video_filename)

        lecture = Lecture.objects.create(
            title=title, professor=professor, video_url=video_url
        )

        return Response({"lecture_id": lecture.id, "video_url": video_url}, status=201)


class LectureListView(generics.ListAPIView):
    queryset = Lecture.objects.all()
    serializer_class = LectureSerializer

    @swagger_auto_schema(
        operation_summary="강의 목록 조회",
        operation_description="모든 강의의 제목과 교수 정보를 리스트로 반환합니다.",
        responses={200: LectureSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class LectureDetailView(generics.RetrieveAPIView):
    queryset = Lecture.objects.all()
    serializer_class = LectureDetailSerializer
    lookup_field = "id"

    @swagger_auto_schema(
        operation_summary="강의 상세 조회",
        operation_description="lecture_id를 기반으로 강의의 상세 정보(제목, 교수, 영상 URL 등)를 반환합니다.",
        responses={200: LectureDetailSerializer()},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
