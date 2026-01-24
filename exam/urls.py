from django.urls import path

from . import views

app_name = 'exam'
urlpatterns = [
    path("<int:topic_id>/mcq/main/", views.MultipleChoiceQuizView.as_view(), name="mcq_for_main_topic"),
    path("<int:topic_id>/mcq/sub/", views.MultipleChoiceQuizView.as_view(), name="mcq_for_sub_topic"),
]
