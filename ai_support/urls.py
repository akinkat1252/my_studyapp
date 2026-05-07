from django.urls import path

from . import views

app_name = 'ai_support'
urlpatterns = [
    path("generate-topic/<int:draft_id>/", views.learning_topic_generate_view, name="learning_topic_generate"),
]