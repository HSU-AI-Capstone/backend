from django.urls import path

from .views import UploadLectureView, LectureListView, LectureDetailView

urlpatterns = [
    path("lectures", UploadLectureView.as_view(), name="upload_lecture"),
    path("lectures/", LectureListView.as_view(), name="lecture_list"),
    path("lectures/<int:id>", LectureDetailView.as_view(), name="lecture_detail"),
]
