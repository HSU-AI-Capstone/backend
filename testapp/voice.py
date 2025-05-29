import os
import re
from pathlib import Path
from textwrap import wrap

from elevenlabs.client import ElevenLabs

# ────────────────────────── #
# 1. 환경 설정
# ────────────────────────── #
EL_API_KEY = os.getenv("EL_API_KEY")
DAWOON_VOICE_ID = os.getenv("DAWOON_VOICE_ID")
JIJUN_VOICE_ID = os.getenv("JIJUN_VOICE_ID")
IU_VOICE_ID = os.getenv("IU_VOICE_ID")
MODEL_ID = "eleven_multilingual_v2"

VOICE_MAP = {
    "DAWOON": DAWOON_VOICE_ID,
    "JIJUN": JIJUN_VOICE_ID,
    "IU": IU_VOICE_ID,
}
DEFAULT_VOICE_KEY = "DAWOON"  # 프론트에서 아무 것도 안 보냈을 때

client = ElevenLabs(api_key=EL_API_KEY)


# ────────────────────────── #
# 2. 텍스트 읽기 & 페이지 분할
# ────────────────────────── #
def read_text_file(txt_path: str) -> str:
    return Path(txt_path).read_text(encoding="utf-8")


def split_pages(text: str) -> list[str]:
    """
    텍스트를 페이지 단위로 분리합니다.

    Args:
        text: 분리할 텍스트

    Returns:
        페이지별 텍스트 리스트
    """
    # 페이지 마커 패턴: "=== Page N ===" 형식
    pattern = r"=== Page \d+ ==="

    # 페이지 마커로 텍스트 분리
    pages = re.split(pattern, text)

    # 첫 번째 빈 페이지 제거 (마커 이전의 텍스트가 없는 경우)
    if pages and not pages[0].strip():
        pages = pages[1:]

    # 각 페이지의 앞뒤 공백 제거
    pages = [page.strip() for page in pages]

    # 빈 페이지 제거
    pages = [page for page in pages if page]

    print(f"분리된 페이지 수: {len(pages)}")
    for i, page in enumerate(pages, 1):
        print(f"페이지 {i} 내용: {page[:100]}...")  # 각 페이지의 처음 100자만 출력

    return pages


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
                paragraph, max_len, break_long_words=False, break_on_hyphens=False
            ):
                yield part


# ────────────────────────── #
# 4. ElevenLabs TTS → MP3 (단일 페이지용)
# ────────────────────────── #
def page_to_mp3(text: str, out_path: str, voice_id: str):
    with open(out_path, "wb") as f:
        for piece in chunk_text(text):
            stream = client.text_to_speech.convert(
                voice_id=voice_id,
                output_format="mp3_44100_128",
                text=piece,
                model_id=MODEL_ID,
            )
            for packet in stream:
                if packet:
                    f.write(packet)
    print(f"✅ Saved → {out_path}")


# ────────────────────────── #
# 5. 전체 TXT → 다중 MP3
# ────────────────────────── #
def tts_pages_to_mp3(
    txt_path: str, out_dir: str, voice_key: str, base_name: str = "page"
) -> list[str]:
    """
    텍스트 파일을 페이지별로 분리하여 MP3 파일로 변환합니다.

    Args:
        txt_path: 텍스트 파일 경로
        out_dir: 출력 디렉토리
        voice_key: 음성 키 ("DAWOON", "JIJUN", "IU" 중 하나)
        base_name: 기본 파일명 (기본값: "page")

    Returns:
        생성된 MP3 파일 경로 리스트
    """
    # 음성 키 검증 및 ID 가져오기
    if voice_key not in VOICE_MAP:
        print(
            f"경고: 잘못된 음성 키 '{voice_key}'. 기본값 '{DEFAULT_VOICE_KEY}'를 사용합니다."
        )
        voice_key = DEFAULT_VOICE_KEY

    voice_id = VOICE_MAP[voice_key]
    print(f"선택된 음성: {voice_key} (ID: {voice_id})")

    # 텍스트 파일 읽기
    with open(txt_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 페이지 분리
    pages = split_pages(text)
    print(f"총 {len(pages)}개의 페이지를 찾았습니다.")

    # 출력 디렉토리 생성
    os.makedirs(out_dir, exist_ok=True)

    # 각 페이지를 MP3로 변환
    mp3_files = []
    for idx, page in enumerate(pages, start=1):
        if not page.strip():  # 빈 페이지 건너뛰기
            print(f"페이지 {idx}가 비어있어 건너뜁니다.")
            continue

        out_path = os.path.join(out_dir, f"{base_name}{idx}.mp3")
        print(f"페이지 {idx} 변환 중: {out_path}")

        try:
            page_to_mp3(page, out_path, voice_id)
            mp3_files.append(out_path)
            print(f"페이지 {idx} 변환 완료")
        except Exception as e:
            print(f"페이지 {idx} 변환 중 오류 발생: {str(e)}")
            raise

    print(f"총 {len(mp3_files)}개의 MP3 파일이 생성되었습니다.")
    return mp3_files


# ────────────────────────── #
# 6. 스크립트 실행 (CLI 테스트용)
#    $ python tts.py --voice iu
# ────────────────────────── #
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--txt", default="./dataset/txt/script_text_page.txt")
    parser.add_argument("--out", default="./dataset/mp3")
    parser.add_argument(
        "--voice", default=DEFAULT_VOICE_KEY, choices=list(VOICE_MAP.keys())
    )
    args = parser.parse_args()

    tts_pages_to_mp3(
        args.txt, args.out, voice_key=args.voice, base_name="el_output_voice"
    )
