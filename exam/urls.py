from django.urls import path

from . import views

app_name = 'exam'
urlpatterns = [
    path("exam/start/per_question/<str:exam_type>/<int:topic_id>/", views.PerQuestionExamStartView.as_view(), name="start_per_question_exam"),
    path("exam/next/per_question/<int:session_id>/", views.PerQuestionExamNextView.as_view(), name="next_per_question_exam"),
    path("exam/end/per_question/<int:session_id>/", views.PerQuestionExamEndView.as_view(), name="end_per_question_exam"),
    path("exam/start/batch/<str:exam_type>/<int:topic_id>/", views.BatchExamStartView.as_view(), name="start_batch_exam"),
    path("exam/next/batch/<int:session_id>/", views.BatchExamNextView.as_view(), name="next_batch_exam"),
    path("exam/end/batch/<int:session_id>/", views.BatchExamEndView.as_view(), name="end_batch_exam"),
]
