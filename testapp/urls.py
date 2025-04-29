from backend.urls import path

# from . import views

# urlpatterns = [
#     path("", views.index),
# ]


# api/urls.py
#from django.urls import path
from .views import CreateLectureTextView # 수정된 뷰 임포트

#app_name = 'api' # 앱 네임스페이스 정의 (선택 사항)

urlpatterns = [
    # POST /api/v1/create-lecture/ 요청을 CreateLectureTextView 로 연결
    path('create-lecture/', CreateLectureTextView.as_view(), name='create-lecture'),
]
