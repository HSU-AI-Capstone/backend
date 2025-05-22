import os
import tempfile
import uuid

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Lecture
from .s3_upload import upload_file_to_s3
from .serializers import (
    LectureSerializer,
    LectureDetailSerializer,
    LectureUploadSerializer,
)
from .utils import mock_generate_lecture_video


class CustomPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 100


class UploadLectureView(APIView):
    parser_classes = [MultiPartParser]

    @swagger_auto_schema(
        operation_summary="강의 업로드",
        operation_description="PDF 파일을 업로드하여 강의 영상을 생성하고, S3에 업로드한 뒤 Lecture 객체를 생성합니다.",
        request_body=LectureUploadSerializer,
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
        serializer = LectureUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subject = serializer.validated_data["subject"]
        description = serializer.validated_data["description"]
        professor = serializer.validated_data["professor"]
        pdf_file = serializer.validated_data["file"]

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, pdf_file.name)
            with open(pdf_path, "wb") as f:
                for chunk in pdf_file.chunks():
                    f.write(chunk)

            video_path = mock_generate_lecture_video(pdf_path)
            # video_path = generate_lecture_video(subject, description, pdf_path)
            video_filename = f"{uuid.uuid4().hex}.mp4"
            video_url = upload_file_to_s3(video_path, video_filename)

        lecture = Lecture.objects.create(
            title=subject,
            professor=professor,
            video_url=video_url,
        )

        return Response({"lecture_id": lecture.id}, status=201)


class LectureListView(generics.ListAPIView):
    queryset = Lecture.objects.all()
    serializer_class = LectureSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "professor"]
    pagination_class = CustomPagination  # ✅ 추가된 부분

    @swagger_auto_schema(
        operation_summary="강의 목록 조회",
        operation_description="""
        모든 강의의 제목과 교수 정보를 리스트로 반환합니다.  
        `search` 쿼리 파라미터를 이용해 제목 또는 교수명으로 검색이 가능하며,  
        `page`와 `page_size` 쿼리 파라미터로 페이지네이션을 적용할 수 있습니다.
        """,
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="강의 제목 또는 교수명 검색어 (부분 매칭 가능)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="조회할 페이지 번호 (기본값 1)",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                description="한 페이지에 조회할 개수 (최대 100)",
                type=openapi.TYPE_INTEGER,
            ),
        ],
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
