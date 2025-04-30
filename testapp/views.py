from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse("설정이 완료되었습니다.")
# Create your views here.

# script_api/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status # HTTP 상태 코드 사용
from drf_yasg.utils import swagger_auto_schema # Swagger 자동 스키마 생성
from drf_yasg import openapi # Swagger 스키마 정의 도구
from openai import APIError # OpenAI API 에러 임포트

from . import utils # 같은 앱 폴더의 utils.py 임포트

# --- Swagger 문서화를 위한 스키마 정의 ---

# 요청 본문(Request Body) 형식 정의
script_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['input_text'], # 필수 필드 지정
    properties={
        'input_text': openapi.Schema(type=openapi.TYPE_STRING, description='스크립트로 변환할 원본 텍스트 내용'),
    },
    example={ # Swagger UI에 표시될 예시 데이터
        'input_text': '파이썬은 배우기 쉽고 강력한 프로그래밍 언어입니다. 다양한 라이브러리를 제공하며 웹 개발, 데이터 분석, 인공지능 등 여러 분야에서 활용됩니다.'
    }
)

# 성공 응답(Response) 형식 정의
script_success_response = openapi.Response(
    description='스크립트 생성 성공',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'generated_script': openapi.Schema(type=openapi.TYPE_STRING, description='생성된 대화형 스크립트')
        }
    ),
    examples={ # Swagger UI에 표시될 예시 응답
        'application/json': {
            'generated_script': '이번 시간에는 파이썬에 대해 함께 알아볼 거예요.\n\n파이썬은 처음 프로그래밍을 접하는 분들도 비교적 쉽게 배울 수 있으면서도 아주 강력한 기능을 가진 언어랍니다. 마치 레고 블록처럼 다양한 기능의 조각(라이브러리라고 불러요)들을 가져와서 원하는 프로그램을 뚝딱 만들 수 있죠. 예를 들어 웹사이트를 만들거나, 복잡한 데이터를 분석하고 시각화하거나, 요즘 핫한 인공지능 모델을 만드는 데에도 널리 쓰인답니다.\n\n오늘 수업 내용을 간단히 정리해볼게요. 파이썬은 배우기 쉽고 강력하며, 웹 개발, 데이터 분석, 인공지능 등 다양한 분야에서 활용되는 아주 유용한 언어라는 점 기억해주세요. 이것으로 이번 수업을 마치겠습니다.'
        }
    }
)

# 오류 응답 형식 정의 (예: 400 Bad Request)
error_response_400 = openapi.Response(
    description='잘못된 요청 (예: input_text 누락 또는 비어있음)',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
    )
)
# 오류 응답 형식 정의 (예: 500 Internal Server Error)
error_response_500 = openapi.Response(
    description='서버 내부 오류 (예: 처리 중 예상치 못한 오류 발생)',
     schema=openapi.Schema(
        type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
    )
)
# 오류 응답 형식 정의 (예: 503 Service Unavailable)
error_response_503 = openapi.Response(
    description='서비스 사용 불가 (예: OpenAI API 오류 또는 클라이언트 미초기화)',
     schema=openapi.Schema(
        type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
    )
)

# --- API 뷰 클래스 정의 ---

class GenerateScriptAPIView(APIView):
    """
    입력 텍스트로부터 대화형 스크립트를 생성하는 API 엔드포인트입니다.
    'input_text'를 포함하는 JSON 본문을 가진 POST 요청을 받습니다.
    생성된 스크립트를 JSON 형식으로 반환합니다.
    """

    # Swagger 문서 자동 생성을 위한 데코레이터
    @swagger_auto_schema(
        request_body=script_request_body, # 요청 본문 스키마 지정
        responses={ # 가능한 응답 코드와 스키마 지정
            200: script_success_response, # 성공 (OK)
            400: error_response_400,      # 잘못된 요청 (Bad Request)
            500: error_response_500,      # 서버 내부 오류 (Internal Server Error)
            503: error_response_503,      # 서비스 사용 불가 (Service Unavailable)
        },
        operation_summary="스크립트 생성", # Swagger UI에 표시될 요약 정보
        operation_description="입력된 텍스트를 사용하여 OpenAI를 통해 한국어 대화형 스크립트를 생성합니다." # 상세 설명
    )
    def post(self, request, *args, **kwargs):
        """
        스크립트 생성을 위한 POST 요청을 처리합니다.
        """
        # 요청 본문(JSON)에서 'input_text' 데이터 추출
        input_text = request.data.get('input_text')

        # 입력값 유효성 검사
        if not input_text or not isinstance(input_text, str) or not input_text.strip():
            return Response(
                {"error": "'input_text' 필드는 필수이며 비어 있을 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST # 400 에러 반환
            )

        try:
            # utils.py의 함수를 호출하여 OpenAI와 상호작용
            generated_script = utils.generate_script_from_text(input_text)
            # 성공 시 생성된 스크립트와 200 OK 상태 반환
            return Response(
                {"generated_script": generated_script},
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            # 입력값 오류 또는 클라이언트 미초기화 오류 처리
            error_message = str(e)
            if "OpenAI 클라이언트가 초기화되지 않았습니다" in error_message:
                 # 클라이언트 초기화 실패는 서비스 문제로 간주 (503)
                 return Response({"error": f"서비스 설정 오류: {error_message}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            else:
                 # 그 외 ValueError는 잘못된 입력으로 간주 (400)
                 return Response({"error": f"잘못된 입력: {error_message}"}, status=status.HTTP_400_BAD_REQUEST)

        except APIError as e:
            # OpenAI API 자체에서 발생한 오류 처리
            print(f"뷰에서 OpenAI API 오류 발생: {e}") # 서버 로그 기록
            return Response(
                {"error": f"OpenAI API 통신 실패: {e}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE # 외부 서비스 문제 (503)
            )
        except Exception as e:
            # 그 외 예상치 못한 모든 오류 처리
            print(f"뷰에서 예상치 못한 오류 발생: {e}") # 서버 로그 기록 (중요!)
            return Response(
                {"error": "스크립트 생성 중 서버 내부 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR # 500 에러 반환
            )
