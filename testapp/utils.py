import os
from functools import lru_cache
from pathlib import Path
from typing import Union

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from TTS.api import TTS


@lru_cache(maxsize=1)
def _load_xtts():
    """xtts_v2 모델을 한 번만 로드해 캐시"""
    return TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")


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

    tts = _load_xtts()
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
output_voice_path = ("./dataset/mp3/output_voice_2.mp3") # 복제한 목소리로 대본을 읽은 결과물

voice_cloning(txt_path, input_voice_path, output_voice_path) 처럼 사용 가능
"""
