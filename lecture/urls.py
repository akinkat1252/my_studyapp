from django.urls import path
from . import views


app_name = 'lecture'
urlpatterns = [
    path('start/<int:sub_topic_id>/', views.LectureStartView.as_view(), name='lecture'),
    path('next/<int:session_id>/', views.LectureNextView.as_view(), name='next_topic'),
    path('chat/<int:session_id>/', views.LectureChatView.as_view(), name='chat'),
    path('end/<int:session_id>/', views.LectureEndView.as_view(), name='end_lecture'),
]
