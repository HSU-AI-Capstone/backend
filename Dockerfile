FROM python:3.10-slim

# 1. 시스템 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    ffmpeg \
    libsndfile1 \
    pkg-config \
    libssl-dev \
    libreoffice-core \
    poppler-utils \
    default-jre-headless \
    libreoffice \
    fonts-nanum \
    fonts-nanum-coding \
    fonts-nanum-extra \
    fonts-noto-cjk \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. Rust 설치 및 설정
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y \
  && . "$HOME/.cargo/env" \
  && rustup default stable \
  && rustup update \
  && rustup target add aarch64-unknown-linux-gnu \
  && rustc --version

# 3. 환경 변수 등록 (비로그인 셸에서도 작동)
ENV PATH="/root/.cargo/bin:$PATH"
ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8
ENV LANGUAGE=ko_KR.UTF-8
ENV LIBREOFFICE_HOME=/usr/lib/libreoffice
ENV HOME=/tmp
ENV RUSTUP_HOME=/root/.rustup
ENV CARGO_HOME=/root/.cargo

# 4. pip 최신화
RUN pip install --upgrade pip setuptools wheel

# 5. 프로젝트 복사 및 설치
WORKDIR /app
COPY . .

# 6. moviepy 별도 설치 (최신 버전)
RUN pip install --no-deps git+https://github.com/Zulko/moviepy.git@v2.1.2

# 7. python-pptx 버전 고정 (Python 3.10 호환)
RUN pip uninstall -y python-pptx \
  && pip install python-pptx==0.6.21

# 8. requirements 설치
RUN pip install -r requirements.txt

# 9. 설치 검증
RUN soffice --version \
  && pdfinfo -v \
  && python -c "from pptx import Presentation; print('python-pptx installed successfully')"
