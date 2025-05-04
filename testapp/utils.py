# utils.py

import os
import openai
import logging
from typing import Optional, Dict, Any 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_FALLBACK_API_KEY") # 실제 키로 교체하거나 환경 변수 설정
MODEL_NAME = "gpt-4o" 

def get_openai_client(api_key: str = API_KEY) -> Optional[openai.OpenAI]:
    """OpenAI 클라이언트를 초기화하고 반환합니다. 실패 시 None을 반환합니다."""
    if not api_key or api_key == "YOUR_FALLBACK_API_KEY":
        logger.error("OpenAI API 키가 설정되지 않았습니다. 환경 변수 'OPENAI_API_KEY' 또는 함수 인자를 확인하세요.")
        return None
    try:
        client = openai.OpenAI(api_key=api_key)
        logger.info("OpenAI 클라이언트가 성공적으로 초기화되었습니다.")
        return client
    except openai.AuthenticationError:
        logger.error("OpenAI 인증 실패. API 키가 올바른지 확인하세요.")
        return None
    except Exception as e:
        logger.error(f"OpenAI 클라이언트 초기화 중 예상치 못한 오류 발생: {e}", exc_info=True)
        return None

# --- 메인 유틸리티 함수: 텍스트를 PPT 구조로 변환 ---
def generate_ppt_structure(
    text_content: str,
    model: str = MODEL_NAME,
    custom_api_key: Optional[str] = None
) -> Optional[str]:

    if not text_content:
        logger.warning("입력 텍스트 내용이 비어있어 처리를 건너뜁니다.")
        return None

    # 사용할 API 키 결정
    api_key_to_use = custom_api_key if custom_api_key else API_KEY

    # OpenAI 클라이언트 가져오기
    client = get_openai_client(api_key=api_key_to_use)
    if not client:
        return None 

    # 시스템 메시지 (프롬프트 엔지니어링)
    system_message = """
    당신은 교육 콘텐츠를 파워포인트 프레젠테이션용으로 구조화하는 데 특화된 AI 어시스턴트입니다.
    주어진 원본 텍스트(수업 계획이나 강의 자료)를 파워포인트 슬라이드 제작에 바로 사용할 수 있도록,
    명확하고 간결하며 논리적으로 구성된 구조로 재포맷하는 것이 당신의 임무입니다.

    주요 지침:
    1.  **주제 식별**: 텍스트 내의 주요 주제와 하위 주제를 파악합니다.
    2.  **슬라이드 제목**: 각 주요 내용 단락이나 섹션의 핵심을 나타내는 명확한 제목을 생성합니다. (예: "## 슬라이드 제목: [핵심 주제]")
    3.  **슬라이드 내용**: 각 슬라이드의 내용은 원본 텍스트를 바탕으로 핵심 정보를 글머리 기호(bullet points, 예: "- 내용 항목")나 간결한 문장으로 요약합니다. 복잡한 내용은 여러 개의 글머리 기호로 나눌 수 있습니다.
    4.  **논리적 흐름 유지**: 원본 텍스트의 의미와 논리적 순서를 최대한 유지합니다.
    5.  **간결성**: 전문 용어나 복잡한 문장보다는 이해하기 쉬운 표현을 사용합니다. 각 슬라이드의 내용은 간결하게 유지합니다.
    6.  **형식**: 결과물은 슬라이드 제목과 내용이 명확히 구분되도록 구조화합니다. 서론("구조화된 내용은 다음과 같습니다:")이나 결론 문구는 포함하지 않고, 구조화된 슬라이드 내용만 바로 시작합니다.
    7.  **언어**: 결과는 한국어로 작성합니다.

    출력 형식 예시:
    ## 슬라이드 제목: 주제 1
    - 핵심 내용 요약 1
    - 핵심 내용 요약 2

    ## 슬라이드 제목: 주제 2 - 하위 주제 A
    - 관련 정보 1
    - 관련 정보 2
    - 관련 정보 3
    """

    # 사용자 메시지
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
                {"role": "user", "content": user_message}
            ],
            temperature=0.5, 
        )

        logger.info("OpenAI로부터 응답을 받았습니다.")
        structured_content = response.choices[0].message.content.strip()

        if not structured_content:
             logger.warning("OpenAI 응답이 비어 있습니다.")
             return None

        return structured_content

    # OpenAI 관련 오류 처리
    except openai.RateLimitError:
        logger.error("OpenAI API 사용량 제한을 초과했습니다. 잠시 후 다시 시도하세요.")
        return None
    except openai.APIConnectionError:
        logger.error("OpenAI API에 연결할 수 없습니다. 네트워크 연결을 확인하세요.")
        return None
    except openai.APIStatusError as e: # 상태 코드 포함 오류 (e.g., 4xx, 5xx)
         logger.error(f"OpenAI API 상태 오류 발생: {e.status_code} - {e.response}")
         return None
    except openai.APIError as e: # 일반적인 API 오류
         logger.error(f"OpenAI API 오류 발생: {e}")
         return None
    except Exception as e: # 그 외 예상치 못한 오류
        logger.error(f"OpenAI API 호출 중 예상치 못한 오류 발생: {e}", exc_info=True)
        return None

# ---텍스트 파일 읽기 헬퍼 함수 ---
def read_text_file(filepath: str) -> Optional[str]:
    """지정된 경로의 텍스트 파일 내용을 읽어옵니다."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"'{filepath}' 파일에서 내용을 성공적으로 읽었습니다.")
        return content
    except FileNotFoundError:
        logger.error(f"오류: 파일 '{filepath}'을(를) 찾을 수 없습니다.")
        return None
    except Exception as e:
        logger.error(f"파일 '{filepath}' 읽기 중 오류 발생: {e}", exc_info=True)
        return None

# ---텍스트 파일 쓰기 헬퍼 함수 ---
def write_text_file(filepath: str, content: str) -> bool:
    """주어진 내용을 지정된 경로의 텍스트 파일에 씁니다."""
    if content is None:
        logger.warning("내용이 없어 파일 쓰기를 건너<0xEB><0x9A><0xB4>니다.")
        return False
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"내용을 '{filepath}' 파일로 성공적으로 저장했습니다.")
        return True
    except Exception as e:
        logger.error(f"파일 '{filepath}' 쓰기 중 오류 발생: {e}", exc_info=True)
        return False

