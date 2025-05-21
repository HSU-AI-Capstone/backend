import os
import shutil
import tempfile
from pathlib import Path

from .create_ppt import build_lecture_video
from .pdf2text import extract_text_from_pdf_content
from .use_gpt import (
    generate_ppt_structure,
    generate_lesson_script,
    generate_and_execute_ppt_code,
)
from .voice import voice_cloning


def mock_generate_lecture_video(pdf_path: str) -> str:
    """
    실제 영상 생성 대신 testapp/static/dummy.mp4를 복사해서 사용하는 테스트용 함수.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))  # backend 기준에서 한 단계 위
    dummy_video_path = os.path.join(
        base_dir, "testapp", "static", "final_lecture_video.mp4"
    )

    if not os.path.exists(dummy_video_path):
        raise FileNotFoundError(
            "해당 mp4 파일이 존재하지 않습니다: " + dummy_video_path
        )

    # 임시 디렉토리에 복사
    temp_dir = tempfile.mkdtemp()
    target_path = os.path.join(temp_dir, "lecture_video.mp4")
    shutil.copyfile(dummy_video_path, target_path)

    return target_path


def generate_lecture_video(subject: str, pdf_path: str) -> str:
    """
    PDF 파일을 기반으로 강의 영상을 생성합니다.

    Args:
        subject: 강의 주제
        pdf_path: PDF 파일 경로

    Returns:
        생성된 강의 영상 파일 경로
    """
    # 임시 디렉토리 생성
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        # 1. PDF에서 텍스트 추출
        with open(pdf_path, "rb") as f:
            pdf_content = f.read()
        extracted_text = extract_text_from_pdf_content(pdf_content)
        if not extracted_text:
            raise ValueError("PDF에서 텍스트를 추출할 수 없습니다.")

        # 2. GPT를 통해 PPT 구조와 대본 생성
        ppt_structure_file = temp_dir / "ppt_structure.txt"
        script_file = temp_dir / "script.txt"

        # 주제와 PDF 텍스트를 결합하여 PPT 구조 생성
        combined_text = f"주제: {subject}\n\n참고 자료:\n{extracted_text}"
        with open(ppt_structure_file, "w", encoding="utf-8") as f:
            f.write(combined_text)

        ppt_structure = generate_ppt_structure(
            input_text_file=str(ppt_structure_file),
            output_ppt_file=str(ppt_structure_file),
        )
        if not ppt_structure:
            raise ValueError("PPT 구조를 생성할 수 없습니다.")

        # 주제와 PDF 텍스트를 결합하여 대본 생성
        script = generate_lesson_script(
            input_text_file=str(ppt_structure_file),  # PPT 구조를 기반으로 대본 생성
            output_script_file=str(script_file),
        )
        if not script:
            raise ValueError("강의 대본을 생성할 수 없습니다.")

        # 3. PPT 생성
        pptx_file = temp_dir / "lecture.pptx"
        ppt_code_file = temp_dir / "generate_ppt.py"

        # PPT 생성 코드 생성 및 실행
        ppt_code = generate_and_execute_ppt_code(
            input_lecture_file=str(ppt_structure_file),
            output_code_file=str(ppt_code_file),
            api_prompt_text=f"주제 '{subject}'에 대한 강의 내용을 바탕으로 python-pptx를 사용하여 PPT를 생성하는 코드를 작성해주세요.",
            example_input_file="ex_input.txt",
            example_output_file="ex_output.txt",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            execute_code=True,
        )
        if not ppt_code:
            raise ValueError("PPT 생성 코드를 생성할 수 없습니다.")

        # 4. 음성 생성
        audio_dir = temp_dir / "audio"
        audio_dir.mkdir(exist_ok=True)

        # 대본을 페이지별로 분리
        pages = script.split("----page")
        for i, page_content in enumerate(
            pages[1:], 1
        ):  # 첫 번째 요소는 빈 문자열이므로 건너뜀
            page_script_file = temp_dir / f"page_{i}_script.txt"
            with open(page_script_file, "w", encoding="utf-8") as f:
                f.write(page_content.strip())

            # 각 페이지별 음성 생성
            output_voice = audio_dir / f"page_{i}_audio.mp3"
            voice_cloning(
                script_path=str(page_script_file),
                input_voice="path/to/reference_voice.wav",  # TODO: 참조 음성 파일 경로 설정 필요
                output_voice=str(output_voice),
                language="ko",
            )

        # 5. 최종 영상 생성
        output_video = temp_dir / "lecture_video.mp4"
        build_lecture_video(
            pptx_file=str(pptx_file),
            audio_dir=str(audio_dir),
            output_path=str(output_video),
        )

        return str(output_video)
