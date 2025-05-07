# ppt_generator_app/utils.py

import openai
import os
import subprocess
import sys
from pathlib import Path
import tempfile  
import logging  

# 로깅 설정
logger = logging.getLogger(__name__)

GPT_MODEL = "gpt-4o"
API_TIMEOUT = 300  

API_PROMPT_TEMPLATE = """
너는 주어진 '수업 내용' 텍스트를 입력받아, 'python-pptx 라이브러리를 사용하여 PPT 슬라이드를 생성' 하는 코드를 출력해야 해. Python 스크립트를 생성하는 AI야
코드 구조는 슬라이드 내용을 담고있는 구조화된 데이터, 스타일링 및 헬퍼 함수, ppt생성 및 저장 함수, 이미지 생성 함수, 이미지 삽입 함수로 구성돼있어

# 강의 내용을 구조화된 데이터로 정의[
- first page는 title로 강의명, points로 이번주 학습주제를 포함해야 해.
- second page부터는 title, points(text와 explanation{text에 대한 간단한 설명}), notes(해당 페이지에 대한 상세한 설명) 포함해야 해.
- last page는 title, points(2페이지부터의 title로 구성), notes를 포함해야 해.
- 사용할 폰트('Malgun Gothic' 또는 'Calibri' 등), 제목 폰트 사이즈(예: 32pt), 본문 폰트 사이즈(예: 18pt)를 적절히 설정해야 해.
- 출력 PPT 파일명은 '수업 내용'에서 파악된 주차 정보를 바탕으로 적절하게 설정해야 해 (예: 'machine_learning_week1.pptx').
- 슬라이드의 총 장수는 입력 텍스트의 내용을 기반으로 자동으로 결정되어야 해.
- 모든 슬라이드의 기본 배경은 흰색으로 설정하고, 필요하다면 페이지 내용에 어울리는 색상을 사용해도 좋아.
- 텍스트의 줄간격은 청중이 쉽게 볼 수 있도록 조정하고, 필요하다면 내용 페이지에 구분선 같은 간단한 도형을 넣어줘.
- 슬라이드 레이아웃은 제목 슬라이드(첫 페이지), 제목 및 내용 레이아웃(내용, 마지막 페이지)을 사용해야 해.
- 코드 내에 각 기능에 대한 상세한 주석을 반드시 포함시켜줘.
- 슬라이드 note에는 해당 페이지의 내용을 자세히 설명하는 내용을 넣어줘.
- 아래 제공될 '수업 내용' 텍스트를 분석하여 위의 요구사항을 만족하는 완전한 Python 스크립트를 생성해줘.
- 생성하는 코드는 **반드시** 다음 구조를 따라야 해:
    1. 필요한 라이브러리 import
    2. 슬라이드 데이터 정의 (딕셔너리 리스트 형태, 위 요구사항 반영)
    3. 스타일링 및 헬퍼 함수 정의 (폰트 설정, 배경 설정, 도형 추가, 슬라이드 내용 채우기 등)
    4. PPT 생성 및 저장 로직 함수 정의 (Presentation 객체 생성, 슬라이드 반복 추가, 저장)
    5. 이미지 생성 함수로 contents_page의 text를 prompt로 전달 (필요시 DALL-E 사용 명시)
    6. 이미지 삽입 함수로 placeholder를 이용해서 텍스트와 이미지 겹침 방지
    7. 메인 실행 블록 (`if __name__ == "__main__":`) 에서 PPT 생성 함수 호출
- 데이터 구조화 시 'explanation'이나 'notes'가 명확하지 않으면, '수업 내용'의 해당 부분을 바탕으로 적절히 요약해서 채워줘.
- 마지막 요약 슬라이드의 points는 이전 내용 슬라이드들의 title 목록으로 구성해줘.
- **중요: 생성된 Python 스크립트의 마지막에는 생성된 PPT 파일의 전체 경로 또는 파일명만 표준 출력(print)으로 출력해야 해. 예: print("generated_presentation.pptx")**
]

다음 '수업 내용' 텍스트를 사용하여 Python 코드만 생성해줘.
"""

BASE_DIR = Path(__file__).resolve().parent
EXAMPLE_INPUT_FILE = BASE_DIR / "ex_input.txt"  
EXAMPLE_OUTPUT_FILE = BASE_DIR / "ex_output.txt"


def _get_ppt_code_from_api(client, lecture_content: str) -> str:
    """
    주어진 프롬프트와 강의 내용을 OpenAI API에 보내고, 생성된 코드를 반환합니다.
    """
    try:
        try:
            example_input = EXAMPLE_INPUT_FILE.read_text(encoding="utf-8")
            example_output = EXAMPLE_OUTPUT_FILE.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.error(f"예시 입력/출력 파일을 찾을 수 없습니다: {EXAMPLE_INPUT_FILE}, {EXAMPLE_OUTPUT_FILE}")
            example_input = "예시 입력 없음"
            example_output = "예시 출력 없음 (Python 코드만 반환)"

        full_prompt = (
            f"{API_PROMPT_TEMPLATE}\n"
            "---\n"
            "--- 예시 입력 ---\n"
            f"{example_input}\n"
            "---\n"
            "--- 예시 출력 ---\n"
            f"{example_output}\n"
            "---\n"
            "위 예시를 참고하여, 아래 실제 수업 내용에 대해 완전한 Python 스크립트를 생성해 주세요.\n"
            "[수업 내용 시작]\n"
            f"{lecture_content}\n"
            "[수업 내용 끝]"
        )

        logger.info(f"OpenAI API 요청 전송 (모델: {GPT_MODEL})...")
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system",
                 "content": "You are an AI assistant that generates complete Python scripts using the python-pptx library based on provided lecture content and formatting instructions. Only return valid Python code. Do not include any text, explanation, or formatting. At the very end of the generated script, print the exact filename of the generated PPTX file to standard output (e.g., print('output.pptx'))."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.5,  # 창의성 조절
            timeout=API_TIMEOUT
        )
        generated_code = response.choices[0].message.content
        logger.info("API 응답을 성공적으로 받았습니다.")

        if generated_code.strip().startswith("```python"):
            generated_code = generated_code.split("```python", 1)[1]
            if "```" in generated_code:
                generated_code = generated_code.rsplit("```", 1)[0]
        elif generated_code.strip().startswith("```"):
            generated_code = generated_code.split("```", 1)[1]
            if "```" in generated_code:
                generated_code = generated_code.rsplit("```", 1)[0]

        return generated_code.strip()

    except openai.APIError as e:
        logger.error(f"OpenAI API 오류 발생: {e}")
        raise 
    except Exception as e:
        logger.error(f"API 코드 생성 중 예기치 않은 오류 발생: {e}")
        raise


def _save_code_to_temp_file(code: str) -> str:
    """
    생성된 Python 코드를 임시 파일에 저장하고 파일 경로를 반환합니다.
    """
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(code)
            temp_script_path = tmp_file.name
        logger.info(f"생성된 Python 코드가 임시 파일 '{temp_script_path}'에 저장되었습니다.")
        return temp_script_path
    except Exception as e:
        logger.error(f"임시 코드 파일 저장 중 오류 발생: {e}")
        raise


def _execute_generated_code(script_path: str, output_dir: Path) -> Path:
    """
    저장된 Python 스크립트를 실행하고, 생성된 PPT 파일 경로를 반환합니다.
    스크립트는 생성된 PPT 파일명을 표준 출력으로 출력해야 합니다.
    """
    logger.info(f"임시 스크립트 '{script_path}' 실행 시도...")
    try:
        process = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=output_dir,  
            check=True  
        )
        logger.info(f"--- '{Path(script_path).name}' 실행 결과 (표준 출력) ---")
        logger.info(process.stdout)
        if process.stderr:
            logger.warning("--- 실행 중 발생한 오류/경고 출력 ---")
            logger.warning(process.stderr)


        output_lines = process.stdout.strip().splitlines()
        if not output_lines:
            raise ValueError("스크립트가 표준 출력으로 PPT 파일명을 출력하지 않았습니다.")

        generated_ppt_filename = output_lines[-1].strip()
        generated_ppt_path = output_dir / generated_ppt_filename

        if not generated_ppt_path.exists():
            raise FileNotFoundError(f"스크립트가 생성했다고 보고한 PPT 파일 '{generated_ppt_path}'을(를) 찾을 수 없습니다.")

        logger.info(f"스크립트 '{Path(script_path).name}'이(가) PPT 파일 '{generated_ppt_path}'을(를) 성공적으로 생성했습니다.")
        return generated_ppt_path

    except subprocess.CalledProcessError as e:
        logger.error(f"스크립트 실행 중 오류 발생 (종료 코드: {e.returncode}):")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        raise ValueError(f"생성된 코드 실행 실패: {e.stderr[:500]}")  
    except Exception as e:
        logger.error(f"스크립트 실행 중 예기치 않은 오류: {e}")
        raise
    finally:
        logger.info(f"임시 스크립트 파일 '{script_path}'을 삭제하지 않고 유지합니다.")


    # --- 메인 함수 (Django view에서 호출) ---
def generate_presentation_from_content(
        lecture_content: str,
        openai_api_key: str,
        output_directory: str = "generated_ppts"  
) -> Path:
    if not lecture_content:
        raise ValueError("강의 내용이 비어있습니다.")
    if not openai_api_key:
        raise ValueError("OpenAI API 키가 제공되지 않았습니다.")

    # OpenAI 클라이언트 초기화
    try:
        client = openai.OpenAI(api_key=openai_api_key)
    except Exception as e:
        logger.error(f"OpenAI 클라이언트 초기화 실패: {e}")
        raise ValueError(f"OpenAI 클라이언트 초기화 실패: {e}")

    # PPT 생성 디렉토리 확인 및 생성
    ppt_output_dir = Path(output_directory)
    ppt_output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"PPT 출력 디렉토리: {ppt_output_dir.resolve()}")

    # 1. API로부터 Python 코드 생성
    generated_code = _get_ppt_code_from_api(client, lecture_content)
    if not generated_code:
        raise ValueError("API로부터 유효한 코드를 생성하지 못했습니다.")

    # 2. 생성된 코드를 임시 파일에 저장
    temp_script_path = _save_code_to_temp_file(generated_code)

    # 3. 저장된 코드 실행하여 PPT 생성 및 경로 반환
    generated_ppt_path = _execute_generated_code(temp_script_path, ppt_output_dir)

    return generated_ppt_path
