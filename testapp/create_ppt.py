# create_ppt.py
import logging
import os
import subprocess
import tempfile
from pathlib import Path

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)

_soffice_last_stderr = ""


def _run_soffice_convert(pptx: Path, outdir: Path) -> int:
    """
    soffice --convert-to pdf ... 명령을 실행하고,
    stderr를 전역 변수에 저장한 뒤 리턴코드를 체크합니다.
    """
    global _soffice_last_stderr
    try:
        # 입력 파일 존재 확인
        if not pptx.exists():
            raise RuntimeError(f"입력 PPTX 파일이 존재하지 않습니다: {pptx}")

        # 입력 파일 크기 확인
        pptx_size = os.path.getsize(pptx)
        if pptx_size == 0:
            raise RuntimeError(f"입력 PPTX 파일이 비어있습니다: {pptx}")
        print(f"입력 PPTX 파일 크기: {pptx_size} bytes")

        # 출력 디렉토리 생성
        outdir.mkdir(parents=True, exist_ok=True)

        # 환경 변수 설정
        env = os.environ.copy()
        env["HOME"] = str(outdir)  # 임시 홈 디렉토리를 출력 디렉토리로 설정
        env["TMPDIR"] = str(outdir)  # 임시 디렉토리를 출력 디렉토리로 설정
        env["PYTHONIOENCODING"] = "utf-8"  # Python I/O 인코딩 설정
        env["LANG"] = "ko_KR.UTF-8"  # 한글 로케일 설정
        env["LC_ALL"] = "ko_KR.UTF-8"
        env["LANGUAGE"] = "ko_KR.UTF-8"

        # LibreOffice 명령 실행
        cmd = [
            "soffice",
            "--headless",
            "--convert-to",
            "pdf:writer_pdf_Export",  # PDF 변환 필터 명시
            "--outdir",
            str(outdir),
            str(pptx),
        ]

        print(f"실행 명령: {' '.join(cmd)}")
        print(f"입력 파일: {pptx}")
        print(f"출력 디렉토리: {outdir}")

        # LibreOffice 프로세스 실행
        proc = subprocess.run(
            cmd, capture_output=True, text=True, env=env, timeout=60  # 타임아웃 60초
        )

        _soffice_last_stderr = proc.stderr or ""
        print(f"LibreOffice stderr: {_soffice_last_stderr}")
        print(f"LibreOffice stdout: {proc.stdout}")

        # 오류 체크
        if proc.returncode != 0:
            raise RuntimeError(
                f"LibreOffice 변환 실패 (코드: {proc.returncode}): {_soffice_last_stderr}"
            )

        # PDF 파일 생성 확인
        pdf_path = outdir / f"{pptx.stem}.pdf"
        if not pdf_path.exists():
            # 대체 파일명 확인
            pdf_files = list(outdir.glob("*.pdf"))
            if pdf_files:
                print(f"찾은 PDF 파일들: {pdf_files}")
                pdf_path = pdf_files[0]
            else:
                raise RuntimeError(f"PDF 파일이 생성되지 않았습니다: {pdf_path}")

        # PDF 파일 크기 확인
        pdf_size = os.path.getsize(pdf_path)
        if pdf_size == 0:
            raise RuntimeError(f"생성된 PDF 파일이 비어있습니다: {pdf_path}")
        print(f"생성된 PDF 파일: {pdf_path} (크기: {pdf_size} bytes)")

        return proc.returncode

    except subprocess.TimeoutExpired:
        raise RuntimeError("LibreOffice 변환 시간 초과")
    except Exception as e:
        raise RuntimeError(f"LibreOffice 변환 중 오류 발생: {str(e)}")


def _capture_stderr_of_last_soffice_run() -> str:
    """
    가장 마지막에 실행된 soffice 호출의 stderr를 반환합니다.
    """
    return _soffice_last_stderr


def _workdir(prefix: str = "lecture_") -> tempfile.TemporaryDirectory:
    """
    요청마다 고유한 임시 디렉터리를 만들고, 블록을 벗어나면
    전체를 지워준다.
    """
    return tempfile.TemporaryDirectory(prefix=prefix)


def _ppt_to_images(pptx: str | Path, slide_dir: Path) -> list[Path]:
    """
    PPTX를 이미지로 변환합니다.

    Args:
        pptx: PPTX 파일 경로 (문자열 또는 Path 객체)
        slide_dir: 이미지 저장 디렉토리

    Returns:
        생성된 이미지 파일 경로 리스트
    """
    # 문자열을 Path 객체로 변환
    pptx_path = Path(pptx)

    slide_dir.mkdir(parents=True, exist_ok=True)
    print(f"슬라이드 디렉토리 생성: {slide_dir}")

    # 임시 PDF 파일 생성
    pdf_dir = slide_dir.parent / "pdf"
    pdf_dir.mkdir(exist_ok=True)
    pdf_path = pdf_dir / f"{pptx_path.stem}.pdf"

    # PPTX를 PDF로 변환
    _run_soffice_convert(pptx_path, pdf_dir)

    # PDF를 이미지로 변환
    try:
        images = convert_from_path(
            pdf_path,
            dpi=300,  # 해상도 설정
            fmt="png",
            thread_count=4,  # 병렬 처리
            grayscale=False,  # 컬러 이미지
            size=(1920, 1080),  # 16:9 비율
        )
    except Exception as e:
        print(f"PDF를 이미지로 변환하는 중 오류 발생: {str(e)}")
        raise RuntimeError(f"PDF를 이미지로 변환하는 중 오류 발생: {str(e)}")

    # 이미지 저장
    slides: list[Path] = []
    for idx, image in enumerate(images, start=1):
        out_path = slide_dir / f"slide_{idx:04d}.png"
        image.save(out_path, "PNG")
        slides.append(out_path)
        print(f"슬라이드 {idx} 저장: {out_path}")

    print(f"총 {len(slides)}개의 슬라이드 생성 완료")
    return slides


def _slide_clip(image_path: Path, audio_path: Path) -> ImageClip:
    audio = AudioFileClip(str(audio_path))
    clip = ImageClip(str(image_path)).set_duration(audio.duration).set_audio(audio)
    return clip


def build_lecture_video(
    pptx_file: str,
    audio_dir: str,
    output_path: str,
    fps: int = 24,
) -> None:
    """PPTX 파일과 오디오 파일들을 합쳐서 MP4 비디오를 생성합니다.

    Args:
        pptx_file: PPTX 파일 경로
        audio_dir: 오디오 파일들이 있는 디렉토리
        output_path: 출력 MP4 파일 경로
        fps: 초당 프레임 수
    """
    # 1. PPTX → 이미지 변환
    slides_dir = Path(audio_dir).parent / "slides"
    slides_dir.mkdir(exist_ok=True)
    print(f"슬라이드 디렉토리 생성: {slides_dir}")

    slides = _ppt_to_images(pptx_file, slides_dir)
    print(f"생성된 슬라이드 수: {len(slides)}")

    # 2. 오디오 파일 목록
    audio_files = sorted(Path(audio_dir).glob("page*.mp3"))
    print(f"찾은 오디오 파일 수: {len(audio_files)}")
    print(f"오디오 파일 목록: {[f.name for f in audio_files]}")

    # 3. 슬라이드 수와 오디오 파일 수가 일치하는지 확인
    if len(slides) != len(audio_files):
        print(
            f"경고: 슬라이드 수({len(slides)})와 오디오 파일 수({len(audio_files)})가 일치하지 않습니다."
        )
        print(
            "대본 생성 시 슬라이드 수에 맞춰 오디오 파일이 생성되었는지 확인해주세요."
        )
        raise ValueError(
            f"슬라이드 수({len(slides)})와 오디오 파일 수({len(audio_files)})가 일치하지 않습니다."
        )

    # 4. 각 슬라이드에 오디오 추가
    clips = []
    for slide_path, audio_path in zip(slides, audio_files):
        # 슬라이드 이미지 로드
        slide = ImageClip(str(slide_path))

        # 오디오 로드
        audio = AudioFileClip(str(audio_path))

        # 슬라이드 지속 시간을 오디오 길이에 맞춤
        slide = slide.set_duration(audio.duration)

        # 오디오 추가
        slide = slide.set_audio(audio)

        clips.append(slide)

    # 5. 모든 클립 연결
    final_clip = concatenate_videoclips(clips)

    # 6. MP4로 저장
    final_clip.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
    )
