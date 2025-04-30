from backend.urls import path
from . import views

urlpatterns = [
    path("", views.index),
]

# script_api/urls.py
#from django.urls import path
#from . import views # 같은 앱 폴더의 views.py를 임포트

app_name = 'script_api' # 앱 네임스페이스 (선택 사항)

urlpatterns = [
    # '/api/generate-script/' URL 경로 요청을 views.GenerateScriptAPIView 클래스가 처리하도록 매핑
    path('generate-script/', views.GenerateScriptAPIView.as_view(), name='generate_script'),
    # 이 앱의 다른 API 엔드포인트가 있다면 여기에 추가
]
