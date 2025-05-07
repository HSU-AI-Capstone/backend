
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
=======
import logging
import os
import subprocess
import tempfile
from contextlib import ExitStack
from pathlib import Path
from typing import Optional, Dict, Any, Union

import fitz
import openai
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from openai import OpenAI
from pdf2image import convert_from_path

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from TTS.api import TTS

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


API_KEY = os.getenv(
    "OPENAI_API_KEY", "YOUR_FALLBACK_API_KEY"
)  # 실제 키로 교체하거나 환경 변수 설정
MODEL_NAME = "gpt-4o"


# --- OpenAI 클라이언트 초기화 ---
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


# --- 메인 유틸리티 함수: 텍스트를 PPT 구조로 변환 ---
def generate_ppt_structure(
    text_content: str, model: str = MODEL_NAME, custom_api_key: Optional[str] = None
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
                {"role": "user", "content": user_message},
            ],
            temperature=0.5,
        )

        logger.info("OpenAI로부터 응답을 받았습니다.")
        structured_content = response.choices[0].message.content.strip()

        if not structured_content:
            logger.warning("OpenAI 응답이 비어 있습니다.")
            return None

        return structured_content

    except Exception as e:
        logger.error(f"PPT 구조 생성 중 오류 발생: {e}", exc_info=True)
        return None


# --- 메인 유틸리티 함수 ---
def process_pdf_for_cleaning(pdf_file: Any) -> Dict[str, Optional[str]]:

    result: Dict[str, Optional[str]] = {
        "raw_text": None,
        "cleaned_text": None,
        "error": None,
    }

    try:
        pdf_content = pdf_file.read()
        logger.info(f"업로드된 PDF 파일에서 {len(pdf_content)} 바이트를 읽었습니다.")

        # 1. 원본 텍스트 추출
        raw_text = _extract_text_from_pdf_content(pdf_content)
        if raw_text is None:
            result["error"] = "PDF에서 텍스트를 추출하지 못했습니다."
            logger.error(result["error"])
            return result
        result["raw_text"] = raw_text

        # 2. LLM을 사용하여 텍스트 정제
        current_api_key = os.getenv("OPENAI_API_KEY")
        if not current_api_key or current_api_key == "YOUR_FALLBACK_API_KEY_IF_NEEDED":
            result["error"] = "OpenAI API 키가 서버에 설정되지 않았습니다."
            logger.error(result["error"])
            return result

        cleaned_text = _clean_text_with_llm(raw_text, current_api_key, MODEL_NAME)
        if cleaned_text is None:
            result["error"] = "언어 모델을 사용하여 텍스트를 정제하는 데 실패했습니다."
            logger.error(result["error"])
            # 정제 실패 시에도 원본 텍스트와 오류 메시지를 반환합니다.
            return result
        result["cleaned_text"] = cleaned_text

        logger.info("PDF 처리 및 정제가 성공적으로 완료되었습니다.")
        return result

    except Exception as e:
        logger.error(f"PDF 처리 중 예상치 못한 오류 발생: {e}", exc_info=True)
        result["error"] = "처리 중 예상치 못한 오류가 발생했습니다."

        return result


# --- 헬퍼 함수: 텍스트 파일 쓰
def write_text_file(filename: str, content: str) -> bool:
    """지정된 파일에 내용을 씁니다."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"'{filename}'에 내용을 성공적으로 썼습니다.")
        return True
    except Exception as e:
        logger.error(f"파일 '{filename}' 쓰기 오류: {e}", exc_info=True)
        return False


def voice_cloning(
    script_path: Union[str, os.PathLike],
    input_voice: Union[str, os.PathLike],
    output_voice: Union[str, os.PathLike],
    language: str = "ko",
) -> str:
    """
    script_path에 있는 텍스트를 input_voice 화자의 목소리로 읽어
    output_voice(MP3)로 저장하고, 저장된 파일 경로를 리턴.
    """
    script_path = Path(script_path)
    if not script_path.is_file():
        raise FileNotFoundError(script_path)

    text = script_path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"{script_path}가 비어 있습니다.")

    output_voice = Path(output_voice)
    output_voice.parent.mkdir(parents=True, exist_ok=True)

    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
    tts.tts_to_file(
        text=text,
        file_path=str(output_voice),
        speaker_wav=str(input_voice),
        language=language,
    )

    print(f"음성 복제 완료! → {output_voice}")
    return str(output_voice)


"""
txt_path = ("./dataset/txt/script_text_2.txt") # 대본 텍스트 파일
input_voice_path = ("./dataset/mp3/input_voice.wav") # 음성 복제할 목소리
output_voice_path = ("./dataset/mp3/output_voice_3.mp3") # 복제한 목소리로 대본을 읽은 결과물

voice_cloning(txt_path, input_voice_path, output_voice_path) # 처럼 사용 가능
"""


# ────────────────────────────────────────────────────────────
# 유틸: 작업 디렉터리 컨텍스트  (요청별로 깨끗하게 쓰고 자동 삭제)
# ────────────────────────────────────────────────────────────
def _workdir(prefix: str = "lecture_") -> tempfile.TemporaryDirectory:
    """
    요청마다 고유한 임시 디렉터리를 만들고, 블록을 벗어나면
    전체를 지워준다.
    """
    return tempfile.TemporaryDirectory(prefix=prefix)


# ────────────────────────────────────────────────────────────
# 1) PPTX ➜ 이미지
# ────────────────────────────────────────────────────────────
def _ppt_to_images(pptx: Path, slide_dir: Path) -> list[Path]:
    """LibreOffice CLI로 pptx → pdf, pdf → PNG 슬라이드 저장"""
    slide_dir.mkdir(parents=True, exist_ok=True)

    # ① PPTX → PDF
    pdf_path = slide_dir / "slides.pdf"
    subprocess.run(
        [
            "soffice",
            "--headless",
            "--invisible",
            "--convert-to",
            "pdf",
            "--outdir",
            str(slide_dir),
            str(pptx),
        ],
        check=True,
        capture_output=True,
    )

    # ② PDF → 이미지
    for idx, page in enumerate(convert_from_path(pdf_path, fmt="png"), start=1):
        page.save(slide_dir / f"slide_{idx:04d}.png", "PNG")

    return sorted(slide_dir.glob("slide_*.png"))  # 정렬 안전


# ────────────────────────────────────────────────────────────
# 2) 이미지 + 오디오 → 단일 클립
# ────────────────────────────────────────────────────────────
def _slide_clip(image_path: Path, audio_path: Path) -> ImageClip:
    audio = AudioFileClip(str(audio_path))
    clip = ImageClip(str(image_path)).with_duration(audio.duration).with_audio(audio)
    return clip


# ────────────────────────────────────────────────────────────
# 3) 최종 빌더
# ────────────────────────────────────────────────────────────
def build_lecture_video(
    pptx_file: str,
    audio_dir: str,
    output_path: str,
    fps: int = 24,
) -> None:
    """
    • 사용 단계는 한 함수로 묶어 단순화
    • 작업이 끝나면 이미지·중간 PDF·임시 오디오 모두 삭제
    • audio_dir 자체도 임시라면 호출측에서 _workdir()로 감싸면 됨
    """
    with _workdir() as temp_root:
        temp_root = Path(temp_root)
        slide_dir = temp_root / "slides"
        pptx = Path(pptx_file).resolve()

        # 1. 이미지 추출
        _ppt_to_images(pptx, slide_dir)

        # 2. 오디오 파일 목록
        audios = sorted(
            Path(audio_dir).glob("*.mp[34]")
            | Path(audio_dir).glob("*.wav")
            | Path(audio_dir).glob("*.m4a")
        )
        slides = sorted(slide_dir.glob("slide_*.png"))
        if len(slides) != len(audios):
            raise ValueError("슬라이드 수와 오디오 수가 일치하지 않습니다.")

        # 3. 비디오 조립 & 자원 회수
        with ExitStack() as stack:
            clips = [
                stack.enter_context(_slide_clip(s, a))
                for s, a in zip(slides, audios, strict=True)
            ]
            final_video = concatenate_videoclips(clips, method="compose")
            final_video.write_videofile(
                output_path,
                fps=fps,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=temp_root / "temp-audio.m4a",
                remove_temp=True,
            )
            final_video.close()  # 명시적 종료


# --- 헬퍼 함수: PDF에서 텍스트 추출 ---
def _extract_text_from_pdf_content(pdf_content: bytes) -> Optional[str]:
    """
    바이트(bytes)로 제공된 PDF 내용에서 페이지별 텍스트를 추출합니다.

    Args:
        pdf_content: PDF 파일의 내용 (바이트).

    Returns:
        페이지 구분자가 포함된 추출된 텍스트 (문자열), 또는 오류 발생 시 None.
    """
    full_text = ""
    try:
        # 메모리에서 PDF 열기
        doc = fitz.open(stream=pdf_content, filetype="pdf")
    except Exception as e:
        logger.error(f"PDF 스트림 열기 오류: {e}", exc_info=True)
        return None  # 열기 실패 시 None 반환

    logger.info(f"{len(doc)} 페이지 PDF에서 텍스트 추출 중...")
    for i, page in enumerate(doc):
        try:
            page_text = page.get_text()
            full_text += f"------Page {i + 1}------\n"  # 페이지 구분자 추가
            full_text += (
                page_text.strip() + "\n\n"
            )  # 각 페이지 끝 공백 제거 및 줄바꿈 추가
        except Exception as e:
            logger.warning(
                f"경고: {i + 1} 페이지 처리 중 오류 발생 - {e}", exc_info=True
            )
            full_text += f"------Page {i + 1}------\n"
            full_text += "[오류: 이 페이지의 텍스트를 추출할 수 없습니다.]\n\n"

    doc.close()
    logger.info("PDF 텍스트 추출 완료.")
    return full_text.strip()  # 최종 결과 앞뒤 공백 제거


# --- 헬퍼 함수: LLM으로 텍스트 정제 ---
def _clean_text_with_llm(text_content: str, api_key: str, model: str) -> Optional[str]:
    if not api_key or api_key.startswith("YOUR_"):  # API 키 유효성 검사
        logger.error("OpenAI API 키가 올바르게 설정되지 않았습니다.")
        return None

    logger.info(f"OpenAI 모델 ({model})을 사용하여 텍스트 정제 시작...")
    try:
        client = OpenAI(api_key=api_key)

        # LLM 프롬프트 (기존과 유사, 명확성 위해 약간 조정)
        prompt = f"""
다음 텍스트는 PDF 프레젠테이션에서 페이지별로 추출되었습니다.
페이지는 '------Page X------'로 구분됩니다.

작업 목표:
1. '------Page X------' 구분자와 각 페이지의 주요 내용은 유지합니다.
2. 반복적인 머리글/바닥글 (예: 회사 로고, 발표 제목, 날짜, 기밀 유지 안내 등 대부분 페이지에 나타나는 요소)을 제거합니다.
3. 페이지 내용 자체에 포함된 슬라이드 번호나 페이지 번호 ('------Page X------' 구분자와 별개)를 제거합니다.
4. 장식용 기호, 불필요한 공백, 깨진 문자 또는 PDF 추출 과정의 잡음(artifact)을 제거합니다.
5. 최종 결과는 페이지 구조('------Page X------')를 유지하면서, 각 페이지 내용이 자연스럽게 읽히도록 적절한 줄바꿈과 띄어쓰기를 사용하여 가독성을 높입니다. 첫 페이지 구분자부터 시작하여 정제된 텍스트만 출력합니다.

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
            temperature=0.2,  # 일관성 있는 결과
        )

        cleaned_text = response.choices[0].message.content.strip()
        logger.info("OpenAI API를 통한 텍스트 정제 성공.")
        return cleaned_text

    except Exception as e:
        logger.error(f"OpenAI API 호출 중 오류 발생: {e}", exc_info=True)
        return None  # 실패 시 None 반환


# ---텍스트 파일 읽기 헬퍼 함수 ---
def read_text_file(filepath: str) -> Optional[str]:
    """지정된 경로의 텍스트 파일 내용을 읽어옵니다."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
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
        logger.warning("내용이 없어 파일 쓰기를 건너뜁니다.")
        return False
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"내용을 '{filepath}' 파일로 성공적으로 저장했습니다.")
    except Exception as e:
        logger.error(f"파일 '{filepath}' 쓰기 중 오류 발생: {e}", exc_info=True)
        return False

