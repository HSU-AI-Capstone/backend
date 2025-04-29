# backend/settings.py 또는 해당하는 프로젝트 설정 파일

import os
from pathlib import Path
from dotenv import load_dotenv
import pymysql # MySQL 사용 시 필요

# PyMySQL을 MySQLdb 인터페이스처럼 사용하도록 설정
pymysql.install_as_MySQLdb()

# --- 기본 경로 설정 ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- .env 파일 로드 ---
# 기존 방식대로 backend.env 파일 로드
env_path = BASE_DIR / "backend.env" # Path 객체 사용 권장
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    print(f"경고: {env_path} 파일을 찾을 수 없습니다. 환경 변수가 로드되지 않았습니다.")

# --- 보안 및 기본 설정 ---
SECRET_KEY = os.getenv("SECRET_KEY", 'django-insecure-default-fallback-key-if-not-set') # .env 파일에 꼭 설정!
if SECRET_KEY == 'django-insecure-default-fallback-key-if-not-set':
     print("경고: SECRET_KEY가 .env 파일에 설정되지 않았습니다. 기본값 사용 중 (보안 취약)")

# DEBUG 설정 (환경 변수 사용 권장)
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
# DEBUG = True # 또는 개발 시 직접 True 설정

# ALLOWED_HOSTS 설정 (환경 변수 사용 권장)
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
# ALLOWED_HOSTS = ["*"] # 개발 시 편의를 위해 사용 가능하나, 배포 시에는 반드시 구체적인 호스트 지정!

# --- 애플리케이션 정의 ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 기존 앱
    "testapp",

    # 새로 추가된 앱
    "script_api",     # OpenAI 스크립트 생성 앱

    # 서드파티 앱
    "rest_framework", # Django REST Framework
    "drf_yasg",       # Swagger/OpenAPI 생성기
    "corsheaders",    # CORS 처리 앱 (✅ 반드시 추가해야 함)
]

# --- 미들웨어 설정 ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware", # ✅ CORS 미들웨어 추가 (CommonMiddleware보다 위에 위치 권장)
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --- URL 및 WSGI 설정 ---
# 프로젝트 이름이 'backend'라고 가정
ROOT_URLCONF = "backend.urls"
WSGI_APPLICATION = "backend.wsgi.application"

# --- 템플릿 설정 ---
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- 데이터베이스 설정 ---
# 기존 MySQL 설정 유지 (✅ 보안을 위해 환경 변수 사용 강력 권장)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'capstone'),         # 환경 변수 사용 권장
        'USER': os.getenv('DB_USER', 'sa'),              # 환경 변수 사용 권장
        'PASSWORD': os.getenv('DB_PASSWORD', '1234'),       # 환경 변수 사용 권장
        'HOST': os.getenv('DB_HOST', 'localhost'),       # 환경 변수 사용 권장 (Docker 사용 시 서비스 이름)
        'PORT': os.getenv('DB_PORT', 3306),              # 환경 변수 사용 권장
        'OPTIONS': {
            'charset': 'utf8mb4',
            # 필요시 추가 옵션 설정
            # 'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
# DATABASES = { # 기존 하드코딩 방식 (참고용, 비권장)
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'capstone',
#         'USER': 'sa',
#         'PASSWORD': '1234',
#         'HOST': 'localhost',
#         'PORT': 3306,
#         'OPTIONS': {
#             'charset': 'utf8mb4',
#         },
#     }
# }


# --- 비밀번호 검증 설정 ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]

# --- 국제화 설정 ---
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True # 시간대 인식 활성화 (권장)

# --- 정적 파일 설정 ---
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles" # 정적 파일들을 모을 디렉토리 (경로 수정: os.path.join 대신 Path 객체 사용)
# STATICFILES_DIRS = [ BASE_DIR / "static", ] # 프로젝트 전역 static 폴더가 있다면 설정

# --- 기본 Primary Key 설정 ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- 사용자 정의 설정: OpenAI ---
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("경고: OPENAI_API_KEY 환경 변수가 'backend.env' 파일에 설정되지 않았습니다.")
    # 서비스 운영에 필수적이라면 여기서 에러 발생 또는 로깅 강화
    # from django.core.exceptions import ImproperlyConfigured
    # raise ImproperlyConfigured("OPENAI_API_KEY 환경 변수를 설정해야 합니다.")

OPENAI_MODEL_ENGINE = os.getenv('OPENAI_MODEL_ENGINE', "gpt-4o") # 환경 변수 우선, 없으면 기본값 사용

# --- 서드파티 라이브러리 설정 ---

# Django REST Framework 설정
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        # DEBUG=True 일 때만 Browsable API 활성화하는 것이 좋음
        'rest_framework.renderers.BrowsableAPIRenderer' if DEBUG else None,
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    # 필요시 인증/권한 설정 추가
    # 'DEFAULT_AUTHENTICATION_CLASSES': [
    #     'rest_framework.authentication.TokenAuthentication', # 예시
    # ],
    # 'DEFAULT_PERMISSION_CLASSES': [
    #     'rest_framework.permissions.IsAuthenticatedOrReadOnly', # 예시
    # ]
}
# None 값을 제거 (BrowsableAPIRenderer가 DEBUG=False일 때 None이 됨)
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    renderer for renderer in REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] if renderer is not None
]


# Swagger (drf-yasg) 설정
SWAGGER_SETTINGS = {
    # 기존 Bearer 토큰 인증 설정 유지
    "SECURITY_DEFINITIONS": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization", # HTTP 헤더 이름
            "in": "header",
            "description": "JWT Token (Ex: Bearer eyJhbG...)" # 설명 추가
        }
    },
    'USE_SESSION_AUTH': False,      # API에서는 세션 인증 비활성화
    'SHOW_REQUEST_HEADERS': True,   # 요청 헤더 보기 활성화 (Swagger UI)
    'PERSIST_AUTH': True,           # Swagger UI에서 인증 정보 유지
    'DEFAULT_INFO': 'backend.urls.api_info', # API 정보를 urls.py 에서 가져오도록 설정 (선택 사항)
}

# DRF Browsable API 로그인/로그아웃 URL (선택 사항)
LOGIN_URL = 'rest_framework:login'
LOGOUT_URL = 'rest_framework:logout'

# CORS 설정 (✅ django-cors-headers 필요)
CORS_ORIGIN_ALLOW_ALL = True # 모든 출처 허용 (개발용). 배포 시에는 아래처럼 특정 출처만 허용 권장
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000", # 예: 프론트엔드 개발 서버 주소
#     "http://127.0.0.1:3000",
#     "https://your-frontend-domain.com", # 예: 실제 프론트엔드 서비스 도메인
# ]
# CORS_ALLOW_CREDENTIALS = True # 쿠키/인증 헤더 허용 시


# import os
# from dotenv import load_dotenv
# from pathlib import Path
# import pymysql

# # PyMySQL을 MySQLdb로 인식하게 설정 (mysqlclient 없이 사용 가능)
# pymysql.install_as_MySQLdb()

# # BASE_DIR 설정
# BASE_DIR = Path(__file__).resolve().parent.parent

# # .env 파일 로드 (backend.env만 사용)
# env_path = os.path.join(BASE_DIR, "backend.env")
# if os.path.exists(env_path):
#     load_dotenv(env_path)

# # SECRET_KEY 로드
# SECRET_KEY = os.getenv("SECRET_KEY")

# # DEBUG 설정
# # DEBUG = os.getenv("DEBUG", "True").lower() == "true"
# DEBUG = True

# # ALLOWED_HOSTS 설정
# # ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
# ALLOWED_HOSTS = ["*"]
# # Application definition
# INSTALLED_APPS = [
#     "django.contrib.admin",
#     "django.contrib.auth",
#     "django.contrib.contenttypes",
#     "django.contrib.sessions",
#     "django.contrib.messages",
#     "django.contrib.staticfiles",
#     "testapp",
#     "rest_framework",
#     "drf_yasg",  # Swagger 추가
# ]

# MIDDLEWARE = [
#     "django.middleware.security.SecurityMiddleware",
#     "django.contrib.sessions.middleware.SessionMiddleware",
#     "django.middleware.common.CommonMiddleware",
#     "django.middleware.csrf.CsrfViewMiddleware",
#     "django.contrib.auth.middleware.AuthenticationMiddleware",
#     "django.contrib.messages.middleware.MessageMiddleware",
#     "django.middleware.clickjacking.XFrameOptionsMiddleware",
# ]

# ROOT_URLCONF = "backend.urls"

# TEMPLATES = [
#     {
#         "BACKEND": "django.template.backends.django.DjangoTemplates",
#         "DIRS": [],
#         "APP_DIRS": True,
#         "OPTIONS": {
#             "context_processors": [
#                 "django.template.context_processors.debug",
#                 "django.template.context_processors.request",
#                 "django.contrib.auth.context_processors.auth",
#                 "django.contrib.messages.context_processors.messages",
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = "backend.wsgi.application"

# # ✅ Database 설정 (환경 변수 기반)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'capstone',  # docker-compose에서 설정한 MYSQL_DATABASE 값
#         'USER': 'sa',  # docker-compose에서 설정한 MYSQL_USER 값
#         'PASSWORD': '1234',  # docker-compose에서 설정한 MYSQL_PASSWORD 값
#         'HOST': 'localhost',  # docker-compose의 서비스 이름 (컨테이너 내부에서 접속할 때 사용)
#         'PORT': 3306,  # 기본 MySQL 포트
#         'OPTIONS': {
#             'charset': 'utf8mb4',  # UTF-8 문자 인코딩 설정 (이모지 지원 포함)
#         },
#     }
# }

# # Password validation
# AUTH_PASSWORD_VALIDATORS = [
#     {
#         "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
#     },
# ]

# # Internationalization
# LANGUAGE_CODE = "ko-kr"
# TIME_ZONE = "Asia/Seoul"
# USE_I18N = True
# USE_TZ = True

# # Static files
# STATIC_URL = "/static/"
# STATIC_ROOT = os.path.join(BASE_DIR, "static")

# # Default primary key field type
# DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# # Swagger 설정
# SWAGGER_SETTINGS = {
#     "SECURITY_DEFINITIONS": {
#         "Bearer": {
#             "type": "apiKey",
#             "name": "Authorization",
#             "in": "header",
#         }
#     },
#     "USE_SESSION_AUTH": False,
# }


# CORS_ORIGIN_ALLOW_ALL = True
