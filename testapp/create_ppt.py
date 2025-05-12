import logging
import subprocess
import tempfile
from contextlib import ExitStack
from pathlib import Path

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)

def _workdir(prefix: str = "lecture_") -> tempfile.TemporaryDirectory:
    """
    요청마다 고유한 임시 디렉터리를 만들고, 블록을 벗어나면
    전체를 지워준다.
    """
    return tempfile.TemporaryDirectory(prefix=prefix)

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

    return sorted(slide_dir.glob("slide_*.png"))

def _slide_clip(image_path: Path, audio_path: Path) -> ImageClip:
    audio = AudioFileClip(str(audio_path))
    clip = (
        ImageClip(str(image_path))
        .with_duration(audio.duration)
        .with_audio(audio)
    )
    return clip

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
            final_video.close() 