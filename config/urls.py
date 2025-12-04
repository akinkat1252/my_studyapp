from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('task_management.urls', namespace='task_management')),
    path('accounts/', include('allauth.urls')),
    path('ai_support/', include('ai_support.urls', namespace='ai_support')),
]
