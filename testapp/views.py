from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse("설정이 완료되었습니다.")
# Create your views here.

# refiner/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser # 파일 파서 임포트
from drf_yasg.utils import swagger_auto_schema # Swagger 데코레이터
from drf_yasg import openapi # Swagger 파라미터 정의

from django.conf import settings # Django 설정 사용
from .utils import extract_text_from_pdf, clean_text_with_llm # 유틸리티 함수 임포트

class PDFRefineView(APIView):
    # 파일 업로드를 처리할 파서 지정
    parser_classes = (MultiPartParser, FormParser)

    # Swagger 문서 자동 생성을 위한 설정
    @swagger_auto_schema(
        operation_description="PDF 파일을 업로드하여 텍스트를 추출하고 OpenAI를 사용해 정제합니다.",
        # 요청 파라미터 정의 (파일 업로드)
        manual_parameters=[
            openapi.Parameter(
                name='pdf_file', # form-data에서 사용할 파라미터 이름
                in_=openapi.IN_FORM, # 파라미터 위치 (폼 데이터)
                description="처리할 PDF 파일.",
                type=openapi.TYPE_FILE, # 파라미터 타입 (파일)
                required=True # 필수 파라미터
            ),
        ],
        # 예상 응답 정의
        responses={
            200: openapi.Response(
                description="성공적으로 텍스트를 정제함",
                # 응답 예시
                examples={
                    "application/json": {
                        "raw_text": "------Page 1------\n원본 내용...\n\n------Page 2------\n더 많은 원본 내용...\n\n",
                        "refined_text": "------Page 1------\n정제된 내용...\n\n------Page 2------\n더 많은 정제된 내용...\n\n"
                    }
                }
            ),
            400: openapi.Response(description="잘못된 요청 (예: 파일 없음, 유효하지 않은 파일, 추출 오류)"),
            500: openapi.Response(description="서버 내부 오류 (예: OpenAI API 오류)"),
            503: openapi.Response(description="서비스 사용 불가 (예: OpenAI API 키 누락 또는 유효하지 않음)")
        }
    )
    def post(self, request, *args, **kwargs):
        """
        업로드된 PDF 파일과 함께 POST 요청을 처리합니다.
        텍스트를 추출하고, OpenAI로 정리한 후, 원본 텍스트와 정제된 텍스트를 반환합니다.
        """
        # 요청에서 'pdf_file' 이름으로 업로드된 파일 가져오기
        pdf_file = request.FILES.get('pdf_file')

        # 파일이 없는 경우 오류 응답
        if not pdf_file:
            return Response(
                {"error": "PDF 파일이 제공되지 않았습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 기본적인 PDF MIME 타입 확인 (속일 수 있지만, 기본적인 검사)
        if not pdf_file.content_type == 'application/pdf':
             return Response(
                {"error": "업로드된 파일이 PDF 형식이 아닙니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --- 1. 텍스트 추출 ---
        raw_text = extract_text_from_pdf(pdf_file)
        # 추출 실패 시 오류 응답
        if raw_text is None:
            return Response(
                {"error": "PDF에서 텍스트를 추출하지 못했습니다. 파일이 손상되었거나, 암호로 보호되어 있거나, 이미지 기반일 수 있습니다."},
                status=status.HTTP_400_BAD_REQUEST # 잘못된 요청으로 처리
            )

        # --- 2. LLM으로 텍스트 정리 ---
        # API 호출 전에 API 키 설정 여부 확인
        if not settings.OPENAI_API_KEY:
             return Response(
                {"error": "서버에 OpenAI API 키가 설정되어 있지 않습니다."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE # 서비스 사용 불가 상태 코드
            )

        cleaned_text = clean_text_with_llm(raw_text)
        # 정리 실패 시 오류 응답
        if cleaned_text is None:
            # 필요시 특정 OpenAI 오류 확인 (예: AuthenticationError)
            # from openai import AuthenticationError
            # try: ... except AuthenticationError: return Response(...)
            return Response(
                {"error": "AI 서비스를 사용하여 텍스트를 정리하는 데 실패했습니다. 서버 로그를 확인하세요."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR # 서버 내부 오류
            )

        # --- 3. 성공 응답 반환 ---
        return Response(
            {
                "raw_text": raw_text,         # (선택 사항) 원본 텍스트 포함
                "refined_text": cleaned_text  # 정제된 텍스트
            },
            status=status.HTTP_200_OK # 성공 상태 코드
        )
