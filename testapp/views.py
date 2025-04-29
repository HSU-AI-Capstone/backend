from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse("설정이 완료되었습니다.")
# Create your views here.

# api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers # serializers 임포트
from drf_yasg.utils import swagger_auto_schema

# --- 유틸리티 함수 및 사용자 정의 예외 임포트 ---
from .utils import (
    create_lecture_text_from_source,
    OpenAIServiceUnavailable,
    OpenAIConfigurationError,
    OpenAIProcessingError
)

# ----- 시리얼라이저 정의 (views.py 내부에 위치) -----
class TextInputSerializer(serializers.Serializer):
    """입력 텍스트 유효성 검사용 시리얼라이저."""
    text = serializers.CharField(
        required=True,
        allow_blank=False,
        style={'base_template': 'textarea.html'}, # Swagger UI에서 textarea로 보이게 함
        help_text="강의 텍스트로 변환할 원본 내용을 입력하세요."
    )

class LectureTextOutputSerializer(serializers.Serializer):
    """생성된 강의 텍스트 출력용 시리얼라이저."""
    lecture_text = serializers.CharField(
        read_only=True,
        help_text="OpenAI를 통해 생성된 강의 텍스트입니다."
    )
# ----- 시리얼라이저 정의 끝 -----


# --- API 뷰 클래스 ---
class CreateLectureTextView(APIView):
    """
    원본 텍스트를 입력받아 OpenAI를 통해 강의용 텍스트를 생성하는 API 엔드포인트.
    """

    @swagger_auto_schema(
        # 요청 본문 형식 정의 (위에서 정의한 시리얼라이저 사용)
        request_body=TextInputSerializer,
        # 응답 형식 및 상태 코드 정의
        responses={
            status.HTTP_200_OK: LectureTextOutputSerializer,
            status.HTTP_400_BAD_REQUEST: "잘못된 요청: 입력 데이터가 유효하지 않습니다.",
            status.HTTP_500_INTERNAL_SERVER_ERROR: "내부 서버 오류: 요청 처리 중 또는 OpenAI 설정/처리 오류가 발생했습니다.",
            status.HTTP_503_SERVICE_UNAVAILABLE: "서비스 사용 불가: OpenAI API 연결 또는 사용량 제한 등의 문제가 발생했습니다.",
        },
        # Swagger UI에 표시될 정보
        operation_summary="강의 텍스트 생성",
        operation_description="제공된 'text' 필드의 내용을 바탕으로 OpenAI 모델을 사용하여 강의 형식의 텍스트를 생성하여 'lecture_text' 필드로 반환합니다."
    )
    def post(self, request, *args, **kwargs):
        """
        POST 요청을 받아 텍스트를 처리하고 강의 텍스트를 생성합니다.
        """
        # 1. 입력 데이터 유효성 검사
        input_serializer = TextInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. 유효성 검사를 통과한 데이터 추출
        text_content = input_serializer.validated_data['text']

        try:
            # 3. 유틸리티 함수를 호출하여 OpenAI 통해 강의 텍스트 생성
            generated_text = create_lecture_text_from_source(text_content)

            # 4. 성공 시, 결과 데이터를 직렬화하여 응답
            output_data = {'lecture_text': generated_text}
            output_serializer = LectureTextOutputSerializer(data=output_data)
            output_serializer.is_valid() # 내부적으로 생성된 데이터이므로 항상 유효함
            return Response(output_serializer.data, status=status.HTTP_200_OK)

        # 5. OpenAI 관련 예외 처리 (utils에서 정의된 예외 사용)
        except (OpenAIServiceUnavailable, OpenAIConfigurationError, OpenAIProcessingError) as e:
            # APIException에서 정의된 상태 코드와 상세 메시지 사용
            return Response({"error": e.detail}, status=e.status_code)

        # 6. 기타 예상치 못한 서버 내부 오류 처리
        except Exception as e:
            print(f"Unexpected error in CreateLectureTextView: {e}") # 서버 로그에 오류 기록
            return Response(
                {"error": "요청을 처리하는 중 예상치 못한 내부 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
