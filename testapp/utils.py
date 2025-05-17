import os
import shutil
import tempfile


def generate_lecture_video(pdf_path: str) -> str:
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
