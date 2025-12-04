from django.urls import path
from . import views


app_name = 'task_management'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('interest-categories/', views.InterestCategoryListView.as_view(), name='interest_category_list'),
    path('interest-categories/add/', views.InterestCategoryCreateView.as_view(), name='interest_category_add'),
    path('interest-categories/<int:pk>/delete/', views.InterestCategoryDeleteView.as_view(), name='interest_category_delete'),
    path('learning-goals/<int:interest_id>', views.LearningGoalListView.as_view(), name='learning_goal_list'),
    path('learning-goals/<int:interest_id>/set/', views.LearningGoalSetView.as_view(), name='learning_goal_set'),
    path('learning-goals/draft/<int:draft_id>/preview/', views.LearningTopicPreviewView.as_view(), name='topic_preview'),
    path('learning-goals/draft/<int:draft_id>/finalize/', views.LearningGoalFinalizeView.as_view(), name='learning_goal_finalize'),
    path('learning-goals/<int:goal_id>/detail/', views.LearningGoalDetailView.as_view(), name='learning_goal_detail'),
    path('learning-goals/<int:goal_id>/delete/', views.LearningGoalDeleteView.as_view(), name='learning_goal_delete'),
]
