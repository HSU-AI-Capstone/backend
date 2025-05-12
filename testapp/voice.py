import logging
import os
from pathlib import Path
from typing import Union

from TTS.api import TTS

logger = logging.getLogger(__name__)


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

    logger.info(f"음성 복제 완료! → {output_voice}")
    return str(output_voice)
