import os, re
from pathlib import Path
from textwrap import wrap
from elevenlabs.client import ElevenLabs

# ────────────────────────── #
# 1. 환경 설정
# ────────────────────────── #
API_KEY  = ""         # ← 실제 키로 바꿔주세요
VOICE_ID = "brs1mKx3KdAFKU7FzvMN"        # 원하는 화자 ID
MODEL_ID = "eleven_multilingual_v2"      # 모델 ID

client = ElevenLabs(api_key=API_KEY)

# ────────────────────────── #
# 2. 텍스트 읽기 & 페이지 분할
# ────────────────────────── #
def read_text_file(txt_path: str) -> str:
    return Path(txt_path).read_text(encoding="utf-8")

def split_pages(raw_text: str, marker_pattern=r"^----page\s+\d+----\s*$") -> list[str]:
    """
    '----page 1----' 같은 행을 기준으로 페이지 단위로 나눈다.
    빈 페이지는 자동으로 제거.
    """
    # 멀티라인 정규식으로 마커 행을 기준 분리
    pages = re.split(marker_pattern, raw_text, flags=re.MULTILINE)
    # 첫 페이지 앞에 빈 문자열이 나올 수 있으므로 strip 후 필터
    return [page.strip() for page in pages if page.strip()]

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
            for part in wrap(
                paragraph,
                max_len,
                break_long_words=False,
                break_on_hyphens=False
            ):
                yield part

# ────────────────────────── #
# 4. ElevenLabs TTS → MP3 (단일 페이지용)
# ────────────────────────── #
def page_to_mp3(text: str, out_path: str):
    """주어진 텍스트(페이지) 하나를 MP3로 저장"""
    # MP3 스트림(제너레이터) 받아서 바로바로 파일에 이어쓰기
    with open(out_path, "wb") as f:
        for piece in chunk_text(text):
            audio_stream = client.text_to_speech.convert(
                voice_id      = VOICE_ID,
                output_format = "mp3_44100_128",
                text          = piece,
                model_id      = MODEL_ID,
            )
            for packet in audio_stream:
                if packet:
                    f.write(packet)
    print(f"✅ Saved → {out_path}")

# ────────────────────────── #
# 5. 전체 TXT → 다중 MP3
# ────────────────────────── #
def tts_pages_to_mp3(txt_path: str, out_dir: str, base_name: str = "output"):
    raw_text = read_text_file(txt_path)
    pages    = split_pages(raw_text)

    # 출력 폴더 준비
    os.makedirs(out_dir, exist_ok=True)

    for idx, page in enumerate(pages, start=1):
        mp3_path = Path(out_dir) / f"{base_name}_page{idx}.mp3"
        page_to_mp3(page, mp3_path)

# ────────────────────────── #
# 6. 스크립트 실행 (예시)
# ────────────────────────── #
if __name__ == "__main__":
    TXT_FILE   = "./dataset/txt/script_text_page.txt"   # 입력 TXT
    OUTPUT_DIR = "./dataset/mp3"                   # MP3 저장 폴더
    tts_pages_to_mp3(TXT_FILE, OUTPUT_DIR, base_name="el_output_voice")
