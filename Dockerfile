FROM python:3.10-slim

# 시스템 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    ffmpeg \
    libsndfile1 \
    pkg-config \
    libssl-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 최신 Rust 설치 (rustc 1.65 이상 보장)
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    . "$HOME/.cargo/env" && \
    rustc --version

# 환경 변수 수동 등록 (비로그인 shell에서도 작동하도록)
ENV PATH="/root/.cargo/bin:$PATH"

# pip 최신화
RUN pip install --upgrade pip setuptools wheel

# 프로젝트 복사 및 설치
WORKDIR /app
COPY . .

# moviepy 별도 설치
RUN pip install --no-deps git+https://github.com/Zulko/moviepy.git@v2.1.2

# requirements 설치
RUN pip install -r requirements.txt
