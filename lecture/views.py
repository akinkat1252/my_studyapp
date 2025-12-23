import markdown
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic, View
from django.utils.safestring import mark_safe

from task_management.models import LearningMainTopic, LearningSubTopic
from .models import LectureSession, LectureLog
from .services import create_new_lecture_session


# Create your views here.
class LectureView(LoginRequiredMixin, View):
    template_name = "lecture/lecture.html"

    def get(self, request, topic_id):
        sub_topic = get_object_or_404(
            LearningSubTopic,
            user=self.request.user,
            id=topic_id,
        )

        session = create_new_lecture_session(user=request.user, sub_topic=sub_topic)

        context = {
            "title": sub_topic.title,
            "session": session,
        }

        return render(request, self.template_name, context)
