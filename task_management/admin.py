from django.apps import apps
from django.contrib import admin

# Register your models here.
app = apps.get_app_config('task_management')
for model in app.get_models():
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
