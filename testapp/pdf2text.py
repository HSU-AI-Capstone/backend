import logging
from typing import Optional

import fitz

logger = logging.getLogger(__name__)


def extract_text_from_pdf_content(pdf_content: bytes) -> Optional[str]:
    """
    바이트(bytes)로 제공된 PDF 내용에서 페이지별 텍스트를 추출합니다.

    Args:
        pdf_content: PDF 파일의 내용 (바이트).

    Returns:
        페이지 구분자가 포함된 추출된 텍스트 (문자열), 또는 오류 발생 시 None.
    """
    full_text = ""
    try:
        # 메모리에서 PDF 열기
        doc = fitz.open(stream=pdf_content, filetype="pdf")
    except Exception as e:
        logger.error(f"PDF 스트림 열기 오류: {e}", exc_info=True)
        return None

    logger.info(f"{len(doc)} 페이지 PDF에서 텍스트 추출 중...")
    for i, page in enumerate(doc):
        try:
            page_text = page.get_text()
            full_text += f"------Page {i + 1}------\n"
            full_text += page_text.strip() + "\n\n"
        except Exception as e:
            logger.warning(
                f"경고: {i + 1} 페이지 처리 중 오류 발생 - {e}", exc_info=True
            )
            full_text += f"------Page {i + 1}------\n"
            full_text += "[오류: 이 페이지의 텍스트를 추출할 수 없습니다.]\n\n"

    doc.close()
    logger.info("PDF 텍스트 추출 완료.")
    return full_text.strip()
