from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('task_management.urls', namespace='task_management')),
    path('accounts/', include('allauth.urls')),
    path('ai_support/', include('ai_support.urls', namespace='ai_support')),
    path('lecture/', include('lecture.urls', namespace='lecture')),
    path('exam/', include('exam.urls', namespace='exam')),
]
