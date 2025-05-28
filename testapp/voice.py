import os, re
from pathlib import Path
from textwrap import wrap
from elevenlabs.client import ElevenLabs

# ────────────────────────── #
# 1. 환경 설정
# ────────────────────────── #
EL_API_KEY        = os.getenv("EL_API_KEY")
DAWOON_VOICE_ID   = os.getenv("DAWOON_VOICE_ID")
JIJUN_VOICE_ID    = os.getenv("JIJUN_VOICE_ID")
IU_VOICE_ID       = os.getenv("IU_VOICE_ID")
MODEL_ID          = "eleven_multilingual_v2"

VOICE_MAP = {
    "DAWOON": DAWOON_VOICE_ID,
    "JIJUN" : JIJUN_VOICE_ID,
    "IU"    : IU_VOICE_ID,
}
DEFAULT_VOICE_KEY = "DAWOON"          # 프론트에서 아무 것도 안 보냈을 때

client = ElevenLabs(api_key=EL_API_KEY)

# ────────────────────────── #
# 2. 텍스트 읽기 & 페이지 분할
# ────────────────────────── #
def read_text_file(txt_path: str) -> str:
    return Path(txt_path).read_text(encoding="utf-8")

def split_pages(raw_text: str, marker_pattern=r"^----page\s+\d+----\s*$") -> list[str]:
    pages = re.split(marker_pattern, raw_text, flags=re.MULTILINE)
    return [p.strip() for p in pages if p.strip()]

# ────────────────────────── #
# 3. (긴 문장 대응) 간단한 청크 함수
# ────────────────────────── #
def chunk_text(text: str, max_len: int = 4500):
    for paragraph in text.splitlines():
        if not paragraph.strip():
            continue
        if len(paragraph) <= max_len:
            yield paragraph
        else:
            for part in wrap(paragraph, max_len,
                             break_long_words=False,
                             break_on_hyphens=False):
                yield part

# ────────────────────────── #
# 4. ElevenLabs TTS → MP3 (단일 페이지용)
# ────────────────────────── #
def page_to_mp3(text: str, out_path: str, voice_id: str):
    with open(out_path, "wb") as f:
        for piece in chunk_text(text):
            stream = client.text_to_speech.convert(
                voice_id      = voice_id,
                output_format = "mp3_44100_128",
                text          = piece,
                model_id      = MODEL_ID,
            )
            for packet in stream:
                if packet:
                    f.write(packet)
    print(f"✅ Saved → {out_path}")

# ────────────────────────── #
# 5. 전체 TXT → 다중 MP3
# ────────────────────────── #
def tts_pages_to_mp3(txt_path: str, out_dir: str,
                     voice_key: str = DEFAULT_VOICE_KEY,
                     base_name: str = "output"):
    voice_id = VOICE_MAP.get(voice_key, VOICE_MAP[DEFAULT_VOICE_KEY])

    raw_text = read_text_file(txt_path)
    pages    = split_pages(raw_text)
    os.makedirs(out_dir, exist_ok=True)

    for idx, page in enumerate(pages, start=1):
        mp3_path = Path(out_dir) / f"{base_name}_page{idx}.mp3"
        page_to_mp3(page, mp3_path, voice_id)

# ────────────────────────── #
# 6. 스크립트 실행 (CLI 테스트용)
#    $ python tts.py --voice iu
# ────────────────────────── #
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--txt",   default="./dataset/txt/script_text_page.txt")
    parser.add_argument("--out",   default="./dataset/mp3")
    parser.add_argument("--voice", default=DEFAULT_VOICE_KEY,
                        choices=list(VOICE_MAP.keys()))
    args = parser.parse_args()

    tts_pages_to_mp3(args.txt, args.out, voice_key=args.voice,
                     base_name="el_output_voice")
