# script_api/utils.py

import os
import openai
from django.conf import settings # Django 설정 사용
from openai import OpenAI, AuthenticationError, APIError # 구체적인 에러 임포트

# --- OpenAI 클라이언트 초기화 ---
# 모듈 로드 시 한 번만 클라이언트를 초기화합니다.
# 초기화 중 발생할 수 있는 AuthenticationError를 처리합니다.
client = None # 초기값 None
try:
    # settings.py에서 API 키를 올바르게 가져오는지 확인
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        print("치명적 오류: settings.py에 OpenAI API 키가 설정되지 않았습니다.")
        # 설정 오류를 명시적으로 발생시킬 수 있습니다.
        # from django.core.exceptions import ImproperlyConfigured
        # raise ImproperlyConfigured("OpenAI API 키가 누락되었습니다.")
    else:
        client = OpenAI(api_key=api_key)
        print("OpenAI 클라이언트 초기화 성공.")
except AuthenticationError as e:
    print(f"치명적 오류: OpenAI 인증 실패. API 키를 확인하세요. 오류: {e}")
    # OpenAI 없이 앱이 작동할 수 없다면, 서비스 시작을 막거나
    # 서비스가 비활성화되었음을 나타내는 플래그를 설정할 수 있습니다.
    client = None # 초기화 실패 시 client는 None 상태 유지
except Exception as e:
    print(f"치명적 오류: OpenAI 클라이언트 초기화 중 예상치 못한 오류 발생: {e}")
    client = None

# --- 스크립트 생성 로직 ---

def generate_script_from_text(input_text: str) -> str:
    """
    입력 텍스트를 받아 OpenAI API를 사용하여 대화형 스크립트를 생성합니다.

    Args:
        input_text: 스크립트로 변환할 텍스트 내용.

    Returns:
        생성된 스크립트 문자열.

    Raises:
        ValueError: input_text가 비어 있거나 OpenAI 클라이언트 초기화 실패 시 발생.
        APIError: OpenAI API 호출 자체에 문제가 있을 경우 발생.
        Exception: 그 외 예상치 못한 오류 발생 시.
    """
    if not client:
        # 클라이언트가 초기화되지 않은 경우 에러 발생
        raise ValueError("OpenAI 클라이언트가 초기화되지 않았습니다. API 키와 설정을 확인하세요.")

    if not input_text or not input_text.strip():
        raise ValueError("입력 텍스트는 비어 있을 수 없습니다.")

    # settings.py에 정의된 모델 사용
    model_engine = settings.OPENAI_MODEL_ENGINE

    # 프롬프트 구성 (원본 스크립트와 동일)
    prompt_instructions = f"""
    당신은 주어진 텍스트 내용을 바탕으로, 실제 사람이 편안하게 진행하는 수업 대본을 작성하는 AI입니다. 다음 요구사항에 맞춰 자연스러운 한국어 구어체 대본을 생성해주세요.

    **주어진 텍스트 (수업 내용):**
    ---
    {input_text}
    ---

    **대본 작성 요구사항:**
    1.  **시작:** "이번 시간에는 [핵심 주제]에 대해 함께 알아볼 거예요." 와 같이 수업의 주제를 명확히 밝히며 시작하세요. 주제는 주어진 텍스트의 핵심 내용을 파악하여 자연스럽게 언급해야 합니다.
    2.  **본문 (중간 페이지):** 주어진 텍스트 내용과 추가로 관련된 내용을 자세히 설명해주세요. 마치 옆에서 설명해 주듯이 친근한 구어체 말투를 사용하세요. 어려운 용어는 쉽게 풀어서 설명하고, 필요하다면 간단한 예시나 비유를 들어 이해를 도와주세요. 내용을 논리적인 흐름에 따라 여러 문단으로 나누어 설명하는 것이 좋습니다. 딱딱한 설명서 느낌이 아니라, 실제 대화처럼 자연스럽게 이어지도록 작성해주세요.
    3.  **마무리 (마지막 페이지):** "오늘 수업 내용을 간단히 정리해볼게요. 그날 배운 주요 내용을 명확하게 요약하며 마무리하세요. "이것으로 이번 수업을 마치겠습니다" 같은 말을 덧붙여도 좋습니다.
    4.  **전체 스타일:** 전체적으로 일관성 있게 친근하고 부드러운 구어체 말투를 사용해주세요. 듣는 사람이 편안하게 느끼고 내용에 집중할 수 있도록, 실제 교수가 말하는 것처럼 생생하게 작성해주세요.

    **출력 형식:**
    위 요구사항에 따라 작성된 완전한 수업 대본 텍스트만 제공해주세요. 다른 부가적인 설명은 포함하지 마세요.
    """

    print(f"'{model_engine}' 모델을 사용하여 스크립트 생성 요청 중...")
    try:
        response = client.chat.completions.create(
            model=model_engine,
            messages=[
                {"role": "system", "content": "당신은 한국어로 수업 대본을 구어체로 작성하는 전문가입니다."},
                {"role": "user", "content": prompt_instructions}
            ],
            temperature=0.7,
            # max_tokens=3000 # 필요시 최대 토큰 길이 설정 고려
        )
        generated_script = response.choices[0].message.content
        print("스크립트 생성 완료.")
        return generated_script.strip() # 앞뒤 공백 제거 후 반환

    except APIError as e:
        # API 관련 오류 처리 (예: 사용량 제한, 서버 문제)
        print(f"OpenAI API 오류 발생: {e}")
        # 필요하다면 특정 API 오류 유형에 따라 다르게 처리하거나, 오류를 다시 발생시킴
        raise APIError(f"OpenAI API 처리 중 오류 발생: {e}") from e
    except Exception as e:
        # 그 외 API 호출 중 발생할 수 있는 다른 오류 처리
        print(f"OpenAI API 호출 중 예상치 못한 오류 발생: {e}")
        raise Exception(f"예상치 못한 오류가 발생했습니다: {e}") from e
