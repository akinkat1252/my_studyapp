from django.urls import path
from . import views


app_name = 'task_management'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('interest-categories/', views.InterestCategoryListView.as_view(), name='interest_category_list'),
    path('interest-categories/add/', views.InterestCategoryCreateView.as_view(), name='interest_category_add'),
    path('interest-categories/<int:pk>/delete/', views.InterestCategoryDeleteView.as_view(), name='interest_category_delete'),
    path('learning-goals/<int:interest_id>', views.LearningGoalListView.as_view(), name='learning_goal_list'),
    path('learning-goals/<int:interest_id>/create/', views.LearningGoalCreateView.as_view(), name='learning_goal_create'),
]