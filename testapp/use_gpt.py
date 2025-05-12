import logging
import os
from typing import Optional

import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_FALLBACK_API_KEY")
MODEL_NAME = "gpt-4o"


def get_openai_client(api_key: str = API_KEY) -> Optional[openai.OpenAI]:
    """OpenAI 클라이언트를 초기화하고 반환합니다. 실패 시 None을 반환합니다."""
    if not api_key or api_key == "YOUR_FALLBACK_API_KEY":
        logger.error(
            "OpenAI API 키가 설정되지 않았습니다. 환경 변수 'OPENAI_API_KEY' 또는 함수 인자를 확인하세요."
        )
        return None
    try:
        client = openai.OpenAI(api_key=api_key)
        logger.info("OpenAI 클라이언트가 성공적으로 초기화되었습니다.")
        return client
    except openai.AuthenticationError:
        logger.error("OpenAI 인증 실패. API 키가 올바른지 확인하세요.")
        return None
    except Exception as e:
        logger.error(
            f"OpenAI 클라이언트 초기화 중 예상치 못한 오류 발생: {e}", exc_info=True
        )
        return None


def generate_ppt_structure(
    text_content: str, model: str = MODEL_NAME, custom_api_key: Optional[str] = None
) -> Optional[str]:
    """텍스트를 PPT 구조로 변환합니다."""
    if not text_content:
        logger.warning("입력 텍스트 내용이 비어있어 처리를 건너뜁니다.")
        return None

    api_key_to_use = custom_api_key if custom_api_key else API_KEY
    client = get_openai_client(api_key=api_key_to_use)
    if not client:
        return None

    system_message = """
    당신은 교육 콘텐츠를 파워포인트 프레젠테이션용으로 구조화하는 데 특화된 AI 어시스턴트입니다.
    주어진 원본 텍스트(수업 계획이나 강의 자료)를 파워포인트 슬라이드 제작에 바로 사용할 수 있도록,
    명확하고 간결하며 논리적으로 구성된 구조로 재포맷하는 것이 당신의 임무입니다.

    주요 지침:
    1.  **주제 식별**: 텍스트 내의 주요 주제와 하위 주제를 파악합니다.
    2.  **슬라이드 제목**: 각 주요 내용 단락이나 섹션의 핵심을 나타내는 명확한 제목을 생성합니다.
    3.  **슬라이드 내용**: 각 슬라이드의 내용은 원본 텍스트를 바탕으로 핵심 정보를 글머리 기호로 요약합니다.
    4.  **논리적 흐름 유지**: 원본 텍스트의 의미와 논리적 순서를 최대한 유지합니다.
    5.  **간결성**: 전문 용어나 복잡한 문장보다는 이해하기 쉬운 표현을 사용합니다.
    6.  **형식**: 결과물은 슬라이드 제목과 내용이 명확히 구분되도록 구조화합니다.
    7.  **언어**: 결과는 한국어로 작성합니다.
    """

    user_message = f"""
    다음 텍스트 내용을 기반으로 파워포인트 프레젠테이션 슬라이드 구조를 생성해주세요:

    --- 원본 텍스트 시작 ---
    {text_content}
    --- 원본 텍스트 끝 ---
    """

    try:
        logger.info(f"OpenAI 모델({model})에 PPT 구조 생성 요청을 보냅니다...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.5,
        )

        structured_content = response.choices[0].message.content.strip()
        if not structured_content:
            logger.warning("OpenAI 응답이 비어 있습니다.")
            return None

        return structured_content

    except Exception as e:
        logger.error(f"OpenAI API 호출 중 오류 발생: {e}", exc_info=True)
        return None


def clean_text_with_llm(text_content: str, api_key: str, model: str) -> Optional[str]:
    """LLM을 사용하여 텍스트를 정제합니다."""
    if not api_key or api_key.startswith("YOUR_"):
        logger.error("OpenAI API 키가 올바르게 설정되지 않았습니다.")
        return None

    logger.info(f"OpenAI 모델 ({model})을 사용하여 텍스트 정제 시작...")
    try:
        client = OpenAI(api_key=api_key)
        prompt = f"""
다음 텍스트는 PDF 프레젠테이션에서 페이지별로 추출되었습니다.
페이지는 '------Page X------'로 구분됩니다.

작업 목표:
1. '------Page X------' 구분자와 각 페이지의 주요 내용은 유지합니다.
2. 반복적인 머리글/바닥글을 제거합니다.
3. 페이지 내용 자체에 포함된 슬라이드 번호나 페이지 번호를 제거합니다.
4. 장식용 기호, 불필요한 공백, 깨진 문자를 제거합니다.
5. 최종 결과는 페이지 구조를 유지하면서, 각 페이지 내용이 자연스럽게 읽히도록 합니다.

--- 원본 텍스트 시작 ---
{text_content}
--- 원본 텍스트 끝 ---

정제된 텍스트:
"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "당신은 텍스트 정제 전문가입니다. PDF 프레젠테이션에서 추출된 텍스트의 페이지 구조를 유지하면서 머리글/바닥글, 페이지 번호, 노이즈를 제거하여 가독성을 높이는 역할을 합니다.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        cleaned_text = response.choices[0].message.content.strip()
        logger.info("OpenAI API를 통한 텍스트 정제 성공.")
        return cleaned_text

    except Exception as e:
        logger.error(f"OpenAI API 호출 중 오류 발생: {e}", exc_info=True)
        return None
