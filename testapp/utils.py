import os
from pathlib import Path
from typing import Union
from pdf2image import convert_from_path
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
import subprocess
import tempfile
from contextlib import ExitStack

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from TTS.api import TTS


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
    clip = (
        ImageClip(str(image_path))
        .with_duration(audio.duration)
        .with_audio(audio)
    )
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
            Path(audio_dir).glob("*.mp[34]") | Path(audio_dir).glob("*.wav") | Path(audio_dir).glob("*.m4a")
        )
        slides = sorted(slide_dir.glob("slide_*.png"))
        if len(slides) != len(audios):
            raise ValueError("슬라이드 수와 오디오 수가 일치하지 않습니다.")

        # 3. 비디오 조립 & 자원 회수
        with ExitStack() as stack:
            clips = [
                stack.enter_context(_slide_clip(s, a)) for s, a in zip(slides, audios, strict=True)
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

        # ExitStack & _workdir 컨텍스트가 끝나면서
        # • clips, audio, 이미지, pdf, temp-root 전부 삭제
