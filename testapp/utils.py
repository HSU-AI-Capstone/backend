# import logging
# import os
# import subprocess
# import tempfile
# from contextlib import ExitStack
# from pathlib import Path
# from typing import Optional, Union, Dict, Any
#
# import fitz  # PyMuPDF
# import openai
# from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
# from openai import OpenAI
# from pdf2image import convert_from_path
#
# os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
# from TTS.api import TTS
#
# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
# )
# logger = logging.getLogger(__name__)
#
#
# API_KEY = os.getenv(
#     "OPENAI_API_KEY", "YOUR_FALLBACK_API_KEY"
# )  # 실제 키로 교체하거나 환경 변수 설정
# MODEL_NAME = "gpt-4o"
#
#
# def get_openai_client(api_key: str = API_KEY) -> Optional[openai.OpenAI]:
#     """OpenAI 클라이언트를 초기화하고 반환합니다. 실패 시 None을 반환합니다."""
#     if not api_key or api_key == "YOUR_FALLBACK_API_KEY":
#         logger.error(
#             "OpenAI API 키가 설정되지 않았습니다. 환경 변수 'OPENAI_API_KEY' 또는 함수 인자를 확인하세요."
#         )
#         return None
#     try:
#         client = openai.OpenAI(api_key=api_key)
#         logger.info("OpenAI 클라이언트가 성공적으로 초기화되었습니다.")
#         return client
#     except openai.AuthenticationError:
#         logger.error("OpenAI 인증 실패. API 키가 올바른지 확인하세요.")
#         return None
#     except Exception as e:
#         logger.error(
#             f"OpenAI 클라이언트 초기화 중 예상치 못한 오류 발생: {e}", exc_info=True
#         )
#         return None
#
#
# API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_FALLBACK_API_KEY_IF_NEEDED")
# MODEL_NAME = "gpt-4o"
#
#
# # --- 헬퍼 함수: PDF에서 텍스트 추출 ---
# def _extract_text_from_pdf_content(pdf_content: bytes) -> Optional[str]:
#     """
#     바이트(bytes)로 제공된 PDF 내용에서 페이지별 텍스트를 추출합니다.
#
#     Args:
#         pdf_content: PDF 파일의 내용 (바이트).
#
#     Returns:
#         페이지 구분자가 포함된 추출된 텍스트 (문자열), 또는 오류 발생 시 None.
#     """
#     full_text = ""
#     try:
#         # 메모리에서 PDF 열기
#         doc = fitz.open(stream=pdf_content, filetype="pdf")
#     except Exception as e:
#         logger.error(f"PDF 스트림 열기 오류: {e}", exc_info=True)
#         return None  # 열기 실패 시 None 반환
#
#     logger.info(f"{len(doc)} 페이지 PDF에서 텍스트 추출 중...")
#     for i, page in enumerate(doc):
#         try:
#             page_text = page.get_text()
#             full_text += f"------Page {i + 1}------\n"  # 페이지 구분자 추가
#             full_text += (
#                 page_text.strip() + "\n\n"
#             )  # 각 페이지 끝 공백 제거 및 줄바꿈 추가
#         except Exception as e:
#             logger.warning(
#                 f"경고: {i + 1} 페이지 처리 중 오류 발생 - {e}", exc_info=True
#             )
#             full_text += f"------Page {i + 1}------\n"
#             full_text += "[오류: 이 페이지의 텍스트를 추출할 수 없습니다.]\n\n"
#
#     doc.close()
#     logger.info("PDF 텍스트 추출 완료.")
#     return full_text.strip()  # 최종 결과 앞뒤 공백 제거
#
#
# # --- 헬퍼 함수: LLM으로 텍스트 정제 ---
# def _clean_text_with_llm(text_content: str, api_key: str, model: str) -> Optional[str]:
#     if not api_key or api_key.startswith("YOUR_"):  # API 키 유효성 검사
#         logger.error("OpenAI API 키가 올바르게 설정되지 않았습니다.")
#         return None
#
#     logger.info(f"OpenAI 모델 ({model})을 사용하여 텍스트 정제 시작...")
#     try:
#         client = OpenAI(api_key=api_key)
#
#         # LLM 프롬프트 (기존과 유사, 명확성 위해 약간 조정)
#         prompt = f"""
# 다음 텍스트는 PDF 프레젠테이션에서 페이지별로 추출되었습니다.
# 페이지는 '------Page X------'로 구분됩니다.
#
# 작업 목표:
# 1. '------Page X------' 구분자와 각 페이지의 주요 내용은 유지합니다.
# 2. 반복적인 머리글/바닥글 (예: 회사 로고, 발표 제목, 날짜, 기밀 유지 안내 등 대부분 페이지에 나타나는 요소)을 제거합니다.
# 3. 페이지 내용 자체에 포함된 슬라이드 번호나 페이지 번호 ('------Page X------' 구분자와 별개)를 제거합니다.
# 4. 장식용 기호, 불필요한 공백, 깨진 문자 또는 PDF 추출 과정의 잡음(artifact)을 제거합니다.
# 5. 최종 결과는 페이지 구조('------Page X------')를 유지하면서, 각 페이지 내용이 자연스럽게 읽히도록 적절한 줄바꿈과 띄어쓰기를 사용하여 가독성을 높입니다. 첫 페이지 구분자부터 시작하여 정제된 텍스트만 출력합니다.
#
# --- 원본 텍스트 시작 ---
# {text_content}
# --- 원본 텍스트 끝 ---
#
# 정제된 텍스트:
# """
#
#         response = client.chat.completions.create(
#             model=model,
#             messages=[
#                 {"role": "system", "content": system_message},
#                 {"role": "user", "content": user_message},
#             ],
#             temperature=0.5,
#         )
#
#         logger.info("OpenAI로부터 응답을 받았습니다.")
#         structured_content = response.choices[0].message.content.strip()
#
#         if not structured_content:
#             logger.warning("OpenAI 응답이 비어 있습니다.")
#             return None
#
#         return structured_content
#
#     # OpenAI 관련 오류 처리
#     except openai.RateLimitError:
#         logger.error("OpenAI API 사용량 제한을 초과했습니다. 잠시 후 다시 시도하세요.")
#         return None
#     except openai.APIConnectionError:
#         logger.error("OpenAI API에 연결할 수 없습니다. 네트워크 연결을 확인하세요.")
#         return None
#     except openai.APIStatusError as e:  # 상태 코드 포함 오류 (e.g., 4xx, 5xx)
#         logger.error(f"OpenAI API 상태 오류 발생: {e.status_code} - {e.response}")
#         return None
#     except openai.APIError as e:  # 일반적인 API 오류
#         logger.error(f"OpenAI API 오류 발생: {e}")
#         return None
#     except Exception as e:  # 그 외 예상치 못한 오류
#         logger.error(f"OpenAI API 호출 중 예상치 못한 오류 발생: {e}", exc_info=True)
#         return None
#
#
# # ---텍스트 파일 읽기 헬퍼 함수 ---
# def read_text_file(filepath: str) -> Optional[str]:
#     """
#     지정된 경로의 텍스트 파일 내용을 읽어옵니다.
#
#     Args:
#         filepath: 읽을 파일의 경로
#
#     Returns:
#         파일의 내용 (문자열), 또는 오류 발생 시 None
#     """
#     try:
#         with open(filepath, "r", encoding="utf-8") as f:
#             content = f.read()
#         logger.info(f"'{filepath}' 파일에서 내용을 성공적으로 읽었습니다.")
#         return content
#     except FileNotFoundError:
#         logger.error(f"오류: 파일 '{filepath}'을(를) 찾을 수 없습니다.")
#         return None
#     except Exception as e:
#         logger.error(f"파일 '{filepath}' 읽기 중 오류 발생: {e}", exc_info=True)
#         return None
#
#
# # --- 메인 유틸리티 함수 ---
# def process_pdf_for_cleaning(pdf_file: Any) -> Dict[str, Optional[str]]:
#
#     result: Dict[str, Optional[str]] = {
#         "raw_text": None,
#         "cleaned_text": None,
#         "error": None,
#     }
#
#     try:
#         pdf_content = pdf_file.read()
#         logger.info(f"업로드된 PDF 파일에서 {len(pdf_content)} 바이트를 읽었습니다.")
#
#         # 1. 원본 텍스트 추출
#         raw_text = _extract_text_from_pdf_content(pdf_content)
#         if raw_text is None:
#             result["error"] = "PDF에서 텍스트를 추출하지 못했습니다."
#             logger.error(result["error"])
#             return result
#         result["raw_text"] = raw_text
#
#         # 2. LLM을 사용하여 텍스트 정제
#         current_api_key = os.getenv("OPENAI_API_KEY")
#         if not current_api_key or current_api_key == "YOUR_FALLBACK_API_KEY_IF_NEEDED":
#             result["error"] = "OpenAI API 키가 서버에 설정되지 않았습니다."
#             logger.error(result["error"])
#             return result
#
#         cleaned_text = _clean_text_with_llm(raw_text, current_api_key, MODEL_NAME)
#         if cleaned_text is None:
#             result["error"] = "언어 모델을 사용하여 텍스트를 정제하는 데 실패했습니다."
#             logger.error(result["error"])
#             # 정제 실패 시에도 원본 텍스트와 오류 메시지를 반환합니다.
#             return result
#         result["cleaned_text"] = cleaned_text
#
#         logger.info("PDF 처리 및 정제가 성공적으로 완료되었습니다.")
#         return result
#
#     except Exception as e:
#         logger.error(f"PDF 처리 중 예상치 못한 오류 발생: {e}", exc_info=True)
#         result["error"] = "처리 중 예상치 못한 오류가 발생했습니다."
#
#         return result
#
#
# def write_text_file(filename: str, content: str) -> bool:
#     """지정된 파일에 내용을 씁니다."""
#     try:
#         with open(filename, "w", encoding="utf-8") as f:
#             f.write(content)
#         logger.info(f"'{filename}'에 내용을 성공적으로 썼습니다.")
#         return True
#     except Exception as e:
#         logger.error(f"파일 '{filename}' 쓰기 오류: {e}", exc_info=True)
#         return False
#
#
# def voice_cloning(
#     script_path: Union[str, os.PathLike],
#     input_voice: Union[str, os.PathLike],
#     output_voice: Union[str, os.PathLike],
#     language: str = "ko",
# ) -> str:
#     """
#     script_path에 있는 텍스트를 input_voice 화자의 목소리로 읽어
#     output_voice(MP3)로 저장하고, 저장된 파일 경로를 리턴.
#     """
#     script_path = Path(script_path)
#     if not script_path.is_file():
#         raise FileNotFoundError(script_path)
#
#     text = script_path.read_text(encoding="utf-8").strip()
#     if not text:
#         raise ValueError(f"{script_path}가 비어 있습니다.")
#
#     output_voice = Path(output_voice)
#     output_voice.parent.mkdir(parents=True, exist_ok=True)
#
#     tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
#     tts.tts_to_file(
#         text=text,
#         file_path=str(output_voice),
#         speaker_wav=str(input_voice),
#         language=language,
#     )
#
#     print(f"음성 복제 완료! → {output_voice}")
#     return str(output_voice)
#
#
# """
# txt_path = ("./dataset/txt/script_text_2.txt") # 대본 텍스트 파일
# input_voice_path = ("./dataset/mp3/input_voice.wav") # 음성 복제할 목소리
# output_voice_path = ("./dataset/mp3/output_voice_3.mp3") # 복제한 목소리로 대본을 읽은 결과물
#
# voice_cloning(txt_path, input_voice_path, output_voice_path) # 처럼 사용 가능
# """
#
#
# # ────────────────────────────────────────────────────────────
# # 유틸: 작업 디렉터리 컨텍스트  (요청별로 깨끗하게 쓰고 자동 삭제)
# # ────────────────────────────────────────────────────────────
# def _workdir(prefix: str = "lecture_") -> tempfile.TemporaryDirectory:
#     """
#     요청마다 고유한 임시 디렉터리를 만들고, 블록을 벗어나면
#     전체를 지워준다.
#     """
#     return tempfile.TemporaryDirectory(prefix=prefix)
#
#
# # ────────────────────────────────────────────────────────────
# # 1) PPTX ➜ 이미지
# # ────────────────────────────────────────────────────────────
# def _ppt_to_images(pptx: Path, slide_dir: Path) -> list[Path]:
#     """LibreOffice CLI로 pptx → pdf, pdf → PNG 슬라이드 저장"""
#     slide_dir.mkdir(parents=True, exist_ok=True)
#
#     # ① PPTX → PDF
#     pdf_path = slide_dir / "slides.pdf"
#     subprocess.run(
#         [
#             "soffice",
#             "--headless",
#             "--invisible",
#             "--convert-to",
#             "pdf",
#             "--outdir",
#             str(slide_dir),
#             str(pptx),
#         ],
#         check=True,
#         capture_output=True,
#     )
#
#     # ② PDF → 이미지
#     for idx, page in enumerate(convert_from_path(pdf_path, fmt="png"), start=1):
#         page.save(slide_dir / f"slide_{idx:04d}.png", "PNG")
#
#     return sorted(slide_dir.glob("slide_*.png"))  # 정렬 안전
#
#
# # ────────────────────────────────────────────────────────────
# # 2) 이미지 + 오디오 → 단일 클립
# # ────────────────────────────────────────────────────────────
# def _slide_clip(image_path: Path, audio_path: Path) -> ImageClip:
#     audio = AudioFileClip(str(audio_path))
#     clip = ImageClip(str(image_path)).with_duration(audio.duration).with_audio(audio)
#     return clip
#
#
# # ────────────────────────────────────────────────────────────
# # 3) 최종 빌더
# # ────────────────────────────────────────────────────────────
# def build_lecture_video(
#     pptx_file: str,
#     audio_dir: str,
#     output_path: str,
#     fps: int = 24,
# ) -> None:
#     """
#     • 사용 단계는 한 함수로 묶어 단순화
#     • 작업이 끝나면 이미지·중간 PDF·임시 오디오 모두 삭제
#     • audio_dir 자체도 임시라면 호출측에서 _workdir()로 감싸면 됨
#     """
#     with _workdir() as temp_root:
#         temp_root = Path(temp_root)
#         slide_dir = temp_root / "slides"
#         pptx = Path(pptx_file).resolve()
#
#         # 1. 이미지 추출
#         _ppt_to_images(pptx, slide_dir)
#
#         # 2. 오디오 파일 목록
#         audios = sorted(
#             Path(audio_dir).glob("*.mp[34]")
#             | Path(audio_dir).glob("*.wav")
#             | Path(audio_dir).glob("*.m4a")
#         )
#         slides = sorted(slide_dir.glob("slide_*.png"))
#         if len(slides) != len(audios):
#             raise ValueError("슬라이드 수와 오디오 수가 일치하지 않습니다.")
#
#         # 3. 비디오 조립 & 자원 회수
#         with ExitStack() as stack:
#             clips = [
#                 stack.enter_context(_slide_clip(s, a))
#                 for s, a in zip(slides, audios, strict=True)
#             ]
#             final_video = concatenate_videoclips(clips, method="compose")
#             final_video.write_videofile(
#                 output_path,
#                 fps=fps,
#                 codec="libx264",
#                 audio_codec="aac",
#                 temp_audiofile=temp_root / "temp-audio.m4a",
#                 remove_temp=True,
#             )
#             final_video.close()  # 명시적 종료
