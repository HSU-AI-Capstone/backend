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
# pdfprocessor/urls.py

"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
# include와 re_path를 모두 사용하므로 둘 다 임포트합니다.
from django.urls import path, include, re_path
from rest_framework.permissions import AllowAny # 기존 코드에서 사용
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import JsonResponse

# 기존의 간단한 홈 페이지 뷰 유지
def home(request):
    return JsonResponse({"message": "Welcome to the API"})

# Swagger 스키마 뷰 설정 (제안된 상세 설명으로 업데이트)
schema_view = get_schema_view(
   openapi.Info(
      # title="Title", # 기존 제목 대신 더 구체적인 제목 사용 가능
      title="PDF Refiner API (and potentially others)", # 또는 프로젝트 전체 API 제목
      default_version='v1',
      # description="Test description", # 기존 설명 대신 더 구체적인 설명 사용
      description="API for processing data, including PDF text extraction and refinement using OpenAI.",
      terms_of_service="https://www.google.com/policies/terms/", # 필요시 수정
      contact=openapi.Contact(email="contact@example.com"),    # 필요시 수정
      license=openapi.License(name="BSD License"),             # 필요시 수정
   ),
   public=True,
   permission_classes=[AllowAny], # 기존 코드와 동일하게 AllowAny 사용
)


urlpatterns = [
    # 기존 루트 경로 유지
    path("", home, name="home"),
    # 기존 admin 경로 유지
    path('admin/', admin.site.urls),

    # --- API v1 경로 ---
    # 기존 testapp 포함 유지
    path('api/v1/testapp/', include('testapp.urls')), # 기존 앱 경로가 testapp/ 로 끝난다고 가정
    # 새로운 refiner 앱 포함 (기존 구조에 맞춰 /api/v1/ 아래에 추가)
    path('api/v1/refiner/', include('refiner.urls', namespace='refiner_api')), # 네임스페이스 추가

    # --- Swagger 및 ReDoc 경로 (기존 re_path 방식 유지) ---
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
