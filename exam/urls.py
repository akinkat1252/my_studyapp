from django.urls import path

from . import views

app_name = 'exam'
urlpatterns = [
    path("exam/start/<str:exam_type>/<int:topic_id>/", views.ExamStartView.as_view(), name="exam_start"),
    path("exam/question/<int:session_id>/", views.ExamQuestionView.as_view(), name="exam_question"),
    
    path("exam/submit/<int:session_id>/", views.ExamSubmitView.as_view(), name="exam_submit"),
    # path("exam/batch/start/<str:exam_type>/<int:topic_id>/", views.BatchExamStartView.as_view(), name="start_batch_exam"),
    # path("exam/batch/<int:session_id>/", views.BatchExamNextView.as_view(), name="next_batch_exam"),
    # path("exam/batch/end/<int:session_id>/", views.BatchExamEndView.as_view(), name="end_batch_exam"),
]
