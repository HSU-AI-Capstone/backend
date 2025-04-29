# api/utils.py
import openai
from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import APIException

# --- 사용자 정의 API 예외 클래스 ---
class OpenAIServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'OpenAI 서비스가 현재 사용 불가능하거나 사용량 제한에 도달했습니다. 잠시 후 다시 시도해 주세요.'
    default_code = 'openai_service_unavailable'

class OpenAIConfigurationError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'OpenAI API 키가 올바르게 설정되지 않았습니다.'
    default_code = 'openai_config_error'

class OpenAIProcessingError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'OpenAI로 요청을 처리하는 중 오류가 발생했습니다.'
    default_code = 'openai_processing_error'

# --- OpenAI 클라이언트 초기화 ---
try:
    # settings.py 에서 불러온 API 키 사용
    openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
except openai.AuthenticationError:
    print("CRITICAL: OpenAI Authentication Failed during client initialization.")
    openai_client = None # 클라이언트 초기화 실패 표시
except Exception as e:
    print(f"CRITICAL: Unexpected error during OpenAI client initialization: {e}")
    openai_client = None

# --- 핵심 강의 텍스트 생성 함수 ---
def create_lecture_text_from_source(text_content, model="gpt-4o"):
    """주어진 원본 텍스트로부터 강의용 텍스트를 생성하고 API 오류를 처리합니다."""
    if not openai_client:
        print("Error: OpenAI client is not initialized.")
        raise OpenAIConfigurationError() # 설정 오류 발생

    # --- 시스템 프롬프트 (강의 텍스트 생성에 초점) ---
    system_message = """
    당신은 주어진 교육 원본 텍스트를 명확하고 이해하기 쉬운 강의 텍스트 초안으로 변환하는 AI 어시스턴트입니다.
    주요 내용을 식별하고 논리적인 흐름으로 재구성하여, 강의나 스터디 자료로 바로 활용할 수 있는 텍스트를 생성하는 것이 목표입니다.

    주요 지침:
    - 주요 주제와 하위 주제를 명확히 구분합니다.
    - 각 섹션이나 주제별로 명확한 제목(헤딩)을 사용합니다.
    - 내용은 간결한 문장이나 글머리 기호(bullet points)로 요약합니다.
    - 원본 텍스트의 핵심 의미와 논리적 흐름을 유지합니다.
    - "변환된 내용은 다음과 같습니다:"와 같은 서론이나 결론 문구는 추가하지 않습니다. 변환된 강의 텍스트 자체만 제공합니다.
    - 결과물은 한국어로 작성합니다.
    """

    user_message = f"""
    다음 원본 내용을 바탕으로 강의 텍스트를 생성해주세요:

    --- 내용 시작 ---
    {text_content}
    --- 내용 끝 ---
    """

    try:
        print(f"\nSending request to OpenAI model ({model})...")
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5, # 응답의 창의성 조절 (낮을수록 결정적)
            # max_tokens=1500, # 필요시 최대 토큰 길이 제한
        )
        print("Received response from OpenAI.")
        lecture_text = response.choices[0].message.content.strip()
        return lecture_text

    # --- OpenAI API 관련 오류 처리 ---
    except openai.AuthenticationError:
        print("Error: OpenAI Authentication Failed during API call.")
        raise OpenAIConfigurationError() # 설정 오류로 간주
    except openai.RateLimitError:
        print("Error: OpenAI API rate limit exceeded.")
        raise OpenAIServiceUnavailable() # 서비스 사용 불가
    except openai.APIConnectionError:
        print("Error: Cannot connect to OpenAI API.")
        raise OpenAIServiceUnavailable(detail='OpenAI API 연결 불가. 네트워크를 확인하세요.')
    except openai.APIError as e: # OpenAI 서버 측 오류 등
        print(f"OpenAI API Error: {e}")
        raise OpenAIProcessingError(detail=f"OpenAI API 오류 발생: {e}")
    except Exception as e: # 기타 예상치 못한 오류
        print(f"Unexpected error during OpenAI API call: {e}")
        raise OpenAIProcessingError(detail=f"예상치 못한 오류 발생: {e}")
