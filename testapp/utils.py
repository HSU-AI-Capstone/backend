# script_api/utils.py
import logging
import os
import subprocess
import tempfile
from contextlib import ExitStack
from pathlib import Path
from typing import Optional, Dict, Any, Union

import fitz
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
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
