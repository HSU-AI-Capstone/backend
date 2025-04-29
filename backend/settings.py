# backend/settings.py
import os
import pymysql
from dotenv import load_dotenv
from pathlib import Path

# PyMySQL을 MySQLdb처럼 사용하도록 설정
pymysql.install_as_MySQLdb()

# --- 기본 경로 설정 ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- 환경 변수 로드 (backend.env 사용) ---
env_path = os.path.join(BASE_DIR, "backend.env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    print(f"Warning: Environment file not found at {env_path}")

# --- 보안 및 기본 설정 (기존 방식 유지) ---
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    print("오류: SECRET_KEY 환경 변수가 backend.env 파일에 설정되지 않았습니다.")
    # 실제 운영 환경에서는 강력한 기본값을 제공하거나 오류를 발생시킬 수 있습니다.
    # SECRET_KEY = 'fallback-secret-key-for-dev' # 개발용 대체 키 예시

# DEBUG 설정 (기존 방식 유지)
# DEBUG = os.getenv("DEBUG", "True").lower() == "true"
DEBUG = True # 현재 코드 기준으로 True 유지

# ALLOWED_HOSTS 설정 (기존 방식 유지)
# ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
ALLOWED_HOSTS = ["*"] # 현재 코드 기준으로 "*" 유지

# --- OpenAI API 키 설정 (새 기능 추가) ---
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("오류: OPENAI_API_KEY 환경 변수가 backend.env 파일에 설정되지 않았습니다.")
    # OpenAI 기능이 필수적이라면 여기서 처리가 필요할 수 있습니다.

# --- 설치된 앱 (기존 앱 + 필요한 앱 확인) ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 기존 앱
    "testapp",
    # 서드파티 앱 (DRF, Swagger 확인)
    "rest_framework",
    "drf_yasg",
    # CORS 헤더 처리 (필요시 주석 해제)
    # "corsheaders",
]

# --- 미들웨어 (기존 목록 유지, CORS 추가시 주석 해제) ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # "corsheaders.middleware.CorsMiddleware", # CORS 사용시 추가
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --- URL 및 템플릿 설정 (기존 방식 유지) ---
ROOT_URLCONF = "backend.urls" # 프로젝트 이름 확인

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

WSGI_APPLICATION = "backend.wsgi.application" # 프로젝트 이름 확인

# --- 데이터베이스 설정 (기존 MySQL 설정 유지) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DATABASE', 'capstone'), # 환경 변수 우선 사용
        'USER': os.getenv('MYSQL_USER', 'sa'),           # 환경 변수 우선 사용
        'PASSWORD': os.getenv('MYSQL_PASSWORD', '1234'), # 환경 변수 우선 사용
        'HOST': os.getenv('MYSQL_HOST', 'localhost'),    # 환경 변수 우선 사용
        'PORT': os.getenv('MYSQL_PORT', 3306),           # 환경 변수 우선 사용
        'OPTIONS': {
            'charset': 'utf8mb4',
            # 'init_command': "SET sql_mode='STRICT_TRANS_TABLES'", # 필요시 SQL 모드 설정
        },
    }
}

# --- 비밀번호 유효성 검사 (기존 목록 유지) ---
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# --- 국제화 설정 (기존 방식 유지) ---
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

# --- 정적 파일 설정 (기존 방식 유지) ---
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# --- 기본 키 필드 타입 ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework 설정 (추가) ---
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        # 개발 환경에서 Browsable API를 사용하려면 아래 줄 주석 해제
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    # 필요하다면 인증, 권한 등 기본 설정 추가 가능
    # 'DEFAULT_AUTHENTICATION_CLASSES': [],
    # 'DEFAULT_PERMISSION_CLASSES': [],
}


# --- Swagger 설정 (기존 + DEFAULT_INFO 추가) ---
SWAGGER_SETTINGS = {
    # 기존 보안 정의 유지
    "SECURITY_DEFINITIONS": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
        }
    },
    # 기존 세션 인증 설정 유지
    "USE_SESSION_AUTH": False,
    # API 정보 경로 추가 (프로젝트 urls.py에서 정의할 api_info 참조)
    'DEFAULT_INFO': 'backend.urls.api_info', # 프로젝트 URLConf 이름 확인!
}

# --- CORS 설정 (기존 방식 유지) ---
# CORS_ALLOW_CREDENTIALS = True # 필요시 쿠키/인증 정보 허용
CORS_ORIGIN_ALLOW_ALL = True # 현재 코드 기준 유지
# 특정 오리진만 허용하려면 아래와 같이 설정
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
#     "https://your-frontend-domain.com",
# ]
# CORS_ALLOW_HEADERS = list(default_headers) + [...] # 필요시 허용 헤더 추가
# CORS_ALLOW_METHODS = list(default_methods) + [...] # 필요시 허용 메서드 추가


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
