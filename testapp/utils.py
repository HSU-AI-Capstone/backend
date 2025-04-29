# refiner/utils.py

import fitz  # PyMuPDF
import os
from openai import OpenAI
from django.conf import settings # Django 설정을 가져오기 위해 임포트

def extract_text_from_pdf(pdf_file_obj):
    """
    PDF 파일 객체 또는 바이트에서 텍스트를 추출합니다.
    메모리에 업로드된 파일이나 파일 바이트를 처리할 수 있습니다.
    """
    full_text = ""
    try:
        # fitz.open은 파일 스트림을 직접 처리할 수 있습니다.
        # 여기서는 내용을 메모리로 읽어옵니다. 매우 큰 파일의 경우,
        # 임시 파일에 먼저 저장하는 방식이 필요할 수 있습니다.
        pdf_content = pdf_file_obj.read() # 업로드된 파일 객체에서 바이트 읽기
        doc = fitz.open(stream=pdf_content, filetype="pdf") # 스트림으로 열기

        print(f"업로드된 PDF에서 텍스트 추출 중...")
        for i, page in enumerate(doc):
            try:
                page_text = page.get_text()
                full_text += f"------Page {i + 1}------\n"
                full_text += page_text + "\n\n"
            except Exception as e:
                print(f"경고: {i+1} 페이지 처리 중 오류 발생 - {e}")
                full_text += f"------Page {i + 1}------\n"
                full_text += "[오류: 이 페이지의 텍스트를 추출할 수 없습니다.]\n\n"
        doc.close()
        print("PDF 텍스트 추출 완료.")
        return full_text
    except Exception as e:
        print(f"오류: PDF 스트림 열기 또는 처리 중 오류 발생 - {e}")
        # 필요시 특정 fitz 오류 처리 추가
        return None


def clean_text_with_llm(text_content):
    """LLM API를 사용하여 텍스트를 정리합니다."""
    # Django 설정에서 API 키와 모델 이름 가져오기
    api_key = settings.OPENAI_API_KEY
    model = settings.OPENAI_MODEL_NAME

    if not api_key: # API 키가 올바르게 로드되었는지 확인
        print("오류: Django 설정에 OpenAI API 키가 구성되지 않았습니다.")
        # 실제 API에서는 여기서 특정 오류 응답을 반환하거나
        # 뷰에서 처리할 예외를 발생시킬 수 있습니다.
        return None

    print("텍스트 정리를 위해 OpenAI API 호출 중...")
    try:
        client = OpenAI(api_key=api_key)
        # LLM에게 보낼 프롬프트 (이전과 동일)
        prompt = f"""
다음 텍스트는 PDF 프레젠테이션에서 추출되었습니다.
페이지별로 나누어져 있으며 '------Page X------' 형식으로 구분됩니다.

작업 목표:
1. 각 페이지 내용을 명확하게 유지합니다.
2. 페이지 상단/하단에 반복적으로 나타나는 헤더나 푸터 (예: 회사 로고, 발표 제목, 날짜 등)를 제거합니다.
3. 슬라이드 번호 또는 페이지 번호 (예: '------Page X------' 구분자 외에 페이지 내용 자체에 포함된 '2', '3', '4' 등의 숫자)를 제거합니다.
4. 내용과 직접 관련 없는 장식용 기호, 불필요한 공백, 깨진 문자 등을 정리합니다.
5. 최종 결과는 원본 페이지 구분을 유지하되 (------Page X------ 형식 사용), 각 페이지 내용이 자연스럽게 읽히도록 적절한 줄바꿈과 띄어쓰기를 사용해 가독성을 높입니다.

--- 원본 텍스트 시작 ---
{text_content}
--- 원본 텍스트 끝 ---

정리된 텍스트:
"""
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "당신은 텍스트 정리 전문가입니다. PDF 프레젠테이션에서 추출된 텍스트를 페이지 구분을 유지하면서 헤더/푸터, 페이지 번호 등을 제거하고 가독성 높게 다듬는 역할을 합니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        cleaned_text = response.choices[0].message.content.strip()
        print("텍스트 정리 완료.")
        return cleaned_text
    except Exception as e:
        print(f"오류: OpenAI API 호출 중 오류 발생 - {e}")
        # 특정 오류(예: RateLimitError, AuthenticationError) 처리 고려
        return None

# API 응답에는 write_text_file 함수가 필요 없지만,
# 서버 측 로깅 등을 위해 남겨둘 수 있습니다.
