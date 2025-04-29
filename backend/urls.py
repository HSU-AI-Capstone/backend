# backend/urls.py

from django.contrib import admin
from django.urls import path, include, re_path # include, re_path 추가 확인
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import JsonResponse

# 기존의 간단한 홈 페이지 뷰 유지
def home(request):
    return JsonResponse({"message": "Welcome to the API"})

# --- Swagger 스키마 뷰 설정 (새로운 API 정보 반영) ---
schema_view = get_schema_view(
   openapi.Info(
      title="강의 텍스트 생성 API", # 여기에 프로젝트/API의 실제 제목 기입
      default_version='v1',
      description="OpenAI를 사용하여 원본 텍스트로부터 강의용 텍스트 초안을 생성하는 API 및 기타 기능", # API 설명 수정/확장
      terms_of_service="https://www.google.com/policies/terms/", # 실제 약관 URL로 변경
      contact=openapi.Contact(email="contact@example.com"),    # 실제 연락처 이메일로 변경
      license=openapi.License(name="BSD License"),             # 라이선스 확인/변경
   ),
   public=True,
   permission_classes=[AllowAny], # 기존 AllowAny 사용
)

# --- settings.SWAGGER_SETTINGS 에서 참조할 정보 ---
# 이 변수는 settings.py의 SWAGGER_SETTINGS['DEFAULT_INFO'] 에서 참조합니다.
api_info = schema_view.info

urlpatterns = [
    # 기존 루트 경로 유지
    path("", home, name="home"),
    # 기존 Admin 경로 유지
    path('admin/', admin.site.urls),

    # '/api/v1/' 경로로 시작하는 URL은 testapp 앱의 urls.py 에서 처리 (기존 설정 유지)
    # 만약 강의 생성 API가 'testapp' 내부에 있다면 이 설정이 맞습니다.
    # 만약 다른 앱('api' 등)에 있다면 해당 앱 이름으로 변경해야 합니다.
    path('api/v1/', include('testapp.urls')), # 앱 이름 확인!

    # 기존 Swagger/ReDoc 경로 유지 (re_path 사용)
    re_path(r'^swagger(?P<format>\\.json|\\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
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
