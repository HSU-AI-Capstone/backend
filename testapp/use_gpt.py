import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, List

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
        client = openai.OpenAI(api_key=API_KEY)
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
    input_text_file: str,
    output_ppt_file: str,
    description: str = "",
    model: str = MODEL_NAME,
    custom_api_key: Optional[str] = None,
) -> Optional[str]:
    """텍스트를 PPT 구조로 변환합니다."""
    text_content = ""
    try:
        logger.info(f"'{input_text_file}' 파일 읽기 시도...")
        with open(input_text_file, "r", encoding="utf-8") as f:
            text_content = f.read()
        if not text_content.strip():
            logger.warning(
                f"'{input_text_file}' 파일이 비어있거나 내용이 없습니다. 처리를 건너뜁니다."
            )
            return None
        logger.info(
            f"'{input_text_file}' 파일 읽기 완료 (내용 길이: {len(text_content)}자)."
        )
    except FileNotFoundError:
        logger.error(
            f"입력 파일 '{input_text_file}'을(를) 찾을 수 없습니다. 파일 경로를 확인해주세요."
        )
        return None
    except Exception as e:
        logger.error(f"'{input_text_file}' 파일 읽기 중 오류 발생: {e}", exc_info=True)
        return None

    system_message = """
    당신은 교육 콘텐츠를 파워포인트 프레젠테이션용으로 구조화하는 데 특화된 AI 어시스턴트입니다.
    주어진 원본 텍스트(수업 계획이나 강의 자료)와 강의 설명을 바탕으로 파워포인트 슬라이드 제작에 바로 사용할 수 있도록,
    명확하고 간결하며 논리적으로 구성된 구조로 재포맷하는 것이 당신의 임무입니다.

    주요 지침:
    1.  **주제 식별**: 텍스트와 강의 설명을 통해 주요 주제와 하위 주제를 파악합니다.
    2.  **슬라이드 제목**: 각 주요 내용 단락이나 섹션의 핵심을 나타내는 명확한 제목을 생성합니다.
    3.  **슬라이드 내용**: 각 슬라이드의 내용은 원본 텍스트와 강의 설명을 바탕으로 핵심 정보를 글머리 기호로 요약합니다.
    4.  **논리적 흐름 유지**: 원본 텍스트의 의미와 논리적 순서를 최대한 유지하면서, 강의 설명에 맞게 내용을 조정합니다.
    5.  **간결성**: 전문 용어나 복잡한 문장보다는 이해하기 쉬운 표현을 사용합니다.
    6.  **형식**: 결과물은 슬라이드 제목과 내용이 명확히 구분되도록 구조화합니다.
    7.  **언어**: 결과는 한국어로 작성합니다.
    """

    user_message = f"""
    다음 텍스트 내용과 강의 설명을 기반으로 파워포인트 프레젠테이션 슬라이드 구조를 생성해주세요:

    --- 강의 설명 ---
    {description}
    --- 강의 설명 끝 ---

    --- 원본 텍스트 시작 ---
    {text_content}
    --- 원본 텍스트 끝 ---
    """

    try:
        client = openai.OpenAI(api_key=openai.api_key)
        logger.info("OpenAI 클라이언트가 성공적으로 초기화되었습니다.")
        return client
    except openai.AuthenticationError:
        logger.error("OpenAI 인증 실패. API 키가 올바른지 확인하세요.")
        return None

    structured_content = None
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

        structured_content_msg = response.choices[0].message.content
        if structured_content_msg:
            structured_content = structured_content_msg.strip()
            if not structured_content:
                logger.warning("OpenAI 응답 내용은 비어 있습니다 (공백만 포함).")
                return None
        else:
            logger.warning("OpenAI 응답의 content 필드가 비어 있습니다.")
            return None

    except openai.APIError as e:
        logger.error(f"OpenAI API 오류 발생: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"OpenAI API 호출 중 예상치 못한 오류 발생: {e}", exc_info=True)
        return None

    if structured_content:
        try:
            logger.info(f"생성된 PPT 구조를 '{output_ppt_file}' 파일로 저장 시도...")
            with open(output_ppt_file, "w", encoding="utf-8") as f:
                f.write(structured_content)
            logger.info(
                f"생성된 PPT 구조를 '{output_ppt_file}' 파일로 성공적으로 저장했습니다."
            )
            return structured_content
        except IOError as e:
            logger.error(
                f"'{output_ppt_file}' 파일 저장 중 입출력 오류 발생: {e}", exc_info=True
            )
            return None
        except Exception as e:
            logger.error(
                f"'{output_ppt_file}' 파일 저장 중 예상치 못한 오류 발생: {e}",
                exc_info=True,
            )
            return None
    else:
        logger.warning("PPT 구조 내용이 없어 파일 저장을 건너뜁니다.")
        return None


def generate_lesson_script(
    input_text_file: str,
    output_script_file: str,
    description: str = "",
    model: str = MODEL_NAME,
    custom_api_key: Optional[str] = None,
    ppt_structure: Optional[List[str]] = None,
) -> Optional[str]:
    """입력 텍스트 파일의 내용을 바탕으로 수업 대본을 생성하고 지정된 파일에 저장합니다."""
    input_text = ""
    try:
        logger.info(f"'{input_text_file}' 파일 읽기 시도...")
        with open(input_text_file, "r", encoding="utf-8") as f:
            input_text = f.read()
        if not input_text.strip():
            logger.warning(
                f"'{input_text_file}' 파일이 비어있습니다. 내용을 확인해주세요."
            )
            return None
        logger.info(
            f"'{input_text_file}' 파일 읽기 완료 (내용 길이: {len(input_text)}자)."
        )
    except FileNotFoundError:
        logger.error(
            f"입력 파일 '{input_text_file}'을(를) 찾을 수 없습니다. 파일 경로를 확인해주세요."
        )
        return None
    except Exception as e:
        logger.error(f"'{input_text_file}' 파일 읽기 중 오류 발생: {e}", exc_info=True)
        return None

    api_key_to_use = custom_api_key if custom_api_key else API_KEY
    client = get_openai_client(api_key=api_key_to_use)
    if not client:
        return None

    # PPT 구조가 있는 경우 프롬프트에 포함
    ppt_context = ""
    if ppt_structure:
        ppt_context = f"""
**PPT 슬라이드 구조:**
{chr(10).join(f'슬라이드 {i+1}: {content}' for i, content in enumerate(ppt_structure))}

위 PPT 슬라이드 구조를 기반으로 각 슬라이드에 맞는 대본을 생성해주세요.
각 페이지는 해당 슬라이드의 내용을 자연스럽게 설명하는 형식이어야 합니다.
"""

    prompt_instructions = f"""
    당신은 주어진 텍스트 내용과 강의 설명을 바탕으로, 실제 사람이 편안하게 진행하는 수업 대본을 작성하는 AI입니다. 
    각 슬라이드의 내용에 맞춰 자연스러운 한국어 구어체 대본을 생성해주세요.

    **강의 설명:**
    ---
    {description}
    ---

    **주어진 텍스트 (수업 내용):**
    ---
    {input_text}
    ---

    {ppt_context}

    **대본 작성 요구사항:**
    1. 각 슬라이드의 내용을 기반으로 해당 슬라이드에 대한 설명 대본을 작성해주세요.
    2. 각 페이지는 "=== Page N ===" 형식으로 구분해주세요 (N은 1부터 시작).
    3. 첫 페이지는 강의 소개와 목차를 포함해야 합니다.
    4. 마지막 페이지는 전체 내용의 요약을 포함해야 합니다.
    5. 각 페이지의 내용은 자연스러운 구어체로 작성해주세요.
    6. 페이지 간의 연결이 자연스럽도록 해주세요.
    7. 전문 용어는 쉽게 설명해주세요.
    8. 각 페이지는 2-3분 정도 발표할 수 있는 분량으로 작성해주세요.
    9. 슬라이드의 내용을 그대로 읽는 것이 아니라, 내용을 이해하기 쉽게 설명하는 방식으로 작성해주세요.
    10. 각 슬라이드의 핵심 내용을 강조하면서도, 자연스러운 설명을 추가해주세요.
    11. 슬라이드의 순서와 내용을 정확히 반영하여 대본을 작성해주세요.
    12. 마지막 페이지는 "=== Page N ===" 형식으로 명확히 구분되어야 합니다.
    """

    try:
        logger.info(f"OpenAI 모델({model})에 대본 생성 요청을 보냅니다...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "당신은 교육 전문가입니다. 주어진 내용을 바탕으로 명확하고 이해하기 쉬운 강의 대본을 작성해주세요. 각 슬라이드의 내용을 자연스럽게 설명하는 방식으로 작성해주세요.",
                },
                {"role": "user", "content": prompt_instructions},
            ],
            temperature=0.7,
        )

        script_content = response.choices[0].message.content
        if not script_content:
            logger.warning("OpenAI 응답의 content 필드가 비어 있습니다.")
            return None

        # 페이지 수 확인
        pages = script_content.split("=== Page")
        if len(pages) < 3:  # 최소 3페이지 (소개, 내용, 요약)
            logger.warning("생성된 대본의 페이지 수가 부족합니다.")
            return None

        # 대본 저장
        try:
            logger.info(f"생성된 대본을 '{output_script_file}' 파일로 저장 시도...")
            with open(output_script_file, "w", encoding="utf-8") as f:
                f.write(script_content)
            logger.info(
                f"생성된 대본을 '{output_script_file}' 파일로 성공적으로 저장했습니다."
            )
            return script_content
        except IOError as e:
            logger.error(
                f"'{output_script_file}' 파일 저장 중 입출력 오류 발생: {e}",
                exc_info=True,
            )
            return None
        except Exception as e:
            logger.error(
                f"'{output_script_file}' 파일 저장 중 예상치 못한 오류 발생: {e}",
                exc_info=True,
            )
            return None
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


def generate_and_execute_ppt_code(
    input_lecture_file: str,
    output_code_file: str,
    api_prompt_text: str,
    example_input_file: str,
    example_output_file: str,
    openai_api_key: str,
    model: str = MODEL_NAME,
    execute_code: bool = True,
) -> Optional[str]:
    """
    강의 내용 텍스트 파일을 기반으로 python-pptx 코드를 생성하고,
    지정된 파일에 저장하며, 실행합니다.
    """

    api_key_to_use = openai_api_key
    client = get_openai_client(api_key=api_key_to_use)
    if not client:
        return None

    lecture_content = ""
    example_input_text = ""
    example_output_code = ""

    try:
        logger.info(f"'{input_lecture_file}' 강의 내용 파일 읽기 시도...")
        lecture_content = Path(input_lecture_file).read_text(encoding="utf-8")
        if not lecture_content.strip():
            logger.warning(f"'{input_lecture_file}' 파일이 비어있습니다.")
            return None
        logger.info(f"'{input_lecture_file}' 파일 읽기 완료.")

        logger.info(f"'{example_input_file}' 예시 입력 파일 읽기 시도...")
        example_input_text = Path(example_input_file).read_text(encoding="utf-8")
        logger.info(f"'{example_input_file}' 파일 읽기 완료.")

        logger.info(f"'{example_output_file}' 예시 출력 파일 읽기 시도...")
        example_output_code = Path(example_output_file).read_text(encoding="utf-8")
        logger.info(f"'{example_output_file}' 파일 읽기 완료.")

    except FileNotFoundError as e:
        logger.error(
            f"필수 입력 파일 중 하나를 찾을 수 없습니다: {e.filename}", exc_info=True
        )
        return None
    except Exception as e:
        logger.error(f"입력 파일 읽기 중 오류 발생: {e}", exc_info=True)
        return None

    full_prompt = (
        f"{api_prompt_text}\n"
        "---\n"
        "--- 예시 입력 ---\n"
        f"{example_input_text}\n"
        "---\n"
        "--- 예시 출력 ---\n"
        f"{example_output_code}\n"
        "---\n"
        "위 예시를 참고하여, 아래 실제 수업 내용에 대해 완전한 Python 스크립트를 생성해 주세요.\n"
        "[수업 내용 시작]\n"
        f"{lecture_content}\n"
        "[수업 내용 끝]"
    )

    generated_code = None
    try:
        logger.info(f"OpenAI API 요청 전송 (모델: {model})...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that generates complete Python scripts using the python-pptx library based on provided lecture content and formatting instructions. Only return valid Python code. Do not include any text, explanation, or formatting.",
                },
                {"role": "user", "content": full_prompt},
            ],
            temperature=0.5,
        )
        raw_generated_content = response.choices[0].message.content
        logger.info("API 응답을 성공적으로 받았습니다.")

        if not raw_generated_content:
            logger.warning("API 응답 내용이 비어있습니다.")
            return None

        if raw_generated_content.strip().startswith("```python"):
            processed_code = raw_generated_content.split("```python", 1)[1]
            if "```" in processed_code:
                processed_code = processed_code.rsplit("```", 1)[0]
        elif raw_generated_content.strip().startswith("```"):
            processed_code = raw_generated_content.split("```", 1)[1]
            if "```" in processed_code:
                processed_code = processed_code.rsplit("```", 1)[0]
        else:
            processed_code = (
                raw_generated_content  # 코드 블록 마커가 없는 경우 그대로 사용
            )

        generated_code = processed_code.strip()
        if not generated_code:
            logger.warning("API 응답에서 추출된 코드가 비어있습니다.")
            return None

    except openai.APIError as e:
        logger.error(f"OpenAI API 오류 발생: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"OpenAI API 호출 중 예상치 못한 오류 발생: {e}", exc_info=True)
        return None

    try:
        logger.info(f"생성된 Python 코드를 '{output_code_file}'에 저장 시도...")
        with open(output_code_file, "w", encoding="utf-8") as f:
            f.write(generated_code)
        logger.info(f"생성된 Python 코드가 '{output_code_file}'에 저장되었습니다.")
    except IOError as e:
        logger.error(
            f"'{output_code_file}' 파일 저장 중 입출력 오류 발생: {e}", exc_info=True
        )
        return None
    except Exception as e:
        logger.error(
            f"'{output_code_file}' 파일 저장 중 예상치 못한 오류 발생: {e}",
            exc_info=True,
        )
        return None

    if execute_code:
        logger.info(f"'{output_code_file}' 실행을 시도합니다...")
        try:
            process = subprocess.run(
                [sys.executable, output_code_file],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            logger.info(f"--- '{output_code_file}' 실행 결과 (표준 출력) ---")
            if process.stdout:
                print(process.stdout)
            else:
                logger.info("표준 출력이 없습니다.")

            if process.stderr:
                logger.warning(
                    f"--- '{output_code_file}' 실행 중 발생한 오류 출력 (표준 오류) ---"
                )
                print(process.stderr)

            logger.info(
                f"스크립트 '{output_code_file}'이(가) 정상적으로 실행되었습니다."
            )
        except subprocess.CalledProcessError as e:
            logger.error(
                f"'{output_code_file}' 실행 중 오류 발생 (종료 코드: {e.returncode}):",
                exc_info=False,
            )
            logger.error(f"표준 출력:\n{e.stdout}")
            logger.error(f"표준 오류:\n{e.stderr}")
        except FileNotFoundError:
            logger.error(
                f"실행할 파일 '{output_code_file}'을(를) 찾을 수 없습니다.",
                exc_info=True,
            )
        except Exception as e:
            logger.error(
                f"'{output_code_file}' 실행 중 예상치 못한 오류 발생: {e}",
                exc_info=True,
            )

    return generated_code
