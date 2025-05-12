# backend/urls.py

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include, re_path  # include와 re_path 추가 확인
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.permissions import (
    AllowAny,
)  # 명시적으로 AllowAny 임포트 (기존 코드 방식 유지)


# --- 간단한 루트 뷰 (기존 코드 유지) ---
def home(request):
    """프로젝트 루트 경로에 대한 간단한 응답"""
    return JsonResponse({"message": "Welcome to the Backend API v1"})


# --- Swagger API 정보 정의 (통합된 정보) ---
# settings.py에서 'DEFAULT_INFO': 'backend.urls.api_info'를 사용한다면 이 변수 이름을 맞춰야 함
api_info = openapi.Info(
    title="Backend Project API",  # ✅ 프로젝트 전체를 나타내는 제목으로 변경
    default_version="v1",
    description="""
    이 문서는 Backend 프로젝트의 API 명세서입니다.
    - **testapp**: 기존 테스트 기능 제공
    - **script_api**: 입력 텍스트 기반 스크립트 생성 기능 제공
    """,  # ✅ 프로젝트의 모든 API 기능을 설명하도록 수정
    terms_of_service="<https://www.google.com/policies/terms/>",  # 필요시 수정
    contact=openapi.Contact(email="your-contact@example.com"),  # ✅ 실제 연락처로 수정
    license=openapi.License(
        name="Your License Type"
    ),  # ✅ 실제 라이선스로 수정 (예: MIT License)
)

schema_view = get_schema_view(
    api_info,  # 위에서 정의한 통합 정보 사용
    public=True,
    permission_classes=[AllowAny],  # 기존 설정 유지
)

# --- URL 패턴 정의 ---
urlpatterns = [
    # 1. 루트 경로
    path("", home, name="home"),  # 기존 루트 경로 유지
    # 2. Django 관리자 페이지
    path("admin/", admin.site.urls),
    # 3. API 엔드포인트 (버전 관리 v1)
    # 기존 testapp 포함 (경로 명확화: /api/v1/test/)
    path("api/v1/test/", include("testapp.urls")),
    # 새로 추가된 script_api 포함 (경로 명확화: /api/v1/script/)
    # path('api/v1/script/', include('script_api.urls')), # ✅ 새로운 앱 URL 추가
    # 4. Swagger 및 ReDoc 문서 경로 (기존 re_path 방식 유지)
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
    # 5. DRF Browsable API를 위한 인증 URL (선택 사항이지만 유용)
    path(
        "api-auth/", include("rest_framework.urls", namespace="rest_framework")
    ),  # ✅ 추가
]


# """
# URL configuration for backend project.

# The `urlpatterns` list routes URLs to views. For more information please see:
#     https://docs.djangoproject.com/en/5.1/topics/http/urls/
# Examples:
# Function views
#     1. Add an import:  from my_app import views
#     2. Add a URL to urlpatterns:  path('', views.home, name='home')
# Class-based views
#     1. Add an import:  from other_app.views import Home
#     2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
# Including another URLconf
#     1. Import the include() function: from django.urls import include, path
#     2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
# """
# from django.contrib import admin
# from django.urls import path, include, re_path
# from rest_framework.permissions import AllowAny
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi
# from django.http import JsonResponse

# # 간단한 홈 페이지 뷰 추가
# def home(request):
#     return JsonResponse({"message": "Welcome to the API"})


# schema_view = get_schema_view(
#    openapi.Info(
#       title="Title",
#       default_version='v1',
#       description="Test description",
#       terms_of_service="<https://www.google.com/policies/terms/>",
#       contact=openapi.Contact(email="contact@snippets.local"),
#       license=openapi.License(name="BSD License"),
#    ),
#    public=True,
#    permission_classes=[AllowAny],
# )


# urlpatterns = [
#     path("", home, name="home"),  # ✅ 루트 경로 추가
#     path('admin/', admin.site.urls),
#     path('api/v1/',include('testapp.urls')),
#     re_path(r'^swagger(?P<format>\\.json|\\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
#     re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
#     re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
# ]
