from backend.urls import path

# from . import views

# urlpatterns = [
#     path("", views.index),
# ]
# refiner/urls.py
from django.urls import path
from .views import PDFRefineView # 만든 뷰 임포트

app_name = 'refiner' # 앱 네임스페이스 설정 (선택 사항)

urlpatterns = [
    # POST 요청을 처리할 API 엔드포인트 URL
    path('refine-pdf/', PDFRefineView.as_view(), name='refine-pdf-api'),
]
