import markdown
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic, View
from django.utils.safestring import mark_safe

from task_management.models import LearningMainTopic, LearningSubTopic
from .models import LectureSession, LectureLog
from .services import create_new_lecture_session
from ai_support.modules.lecture.generate_lecture import generate_lecture_outline


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
        generated_outline = generate_lecture_outline(session=session)
        print(generated_outline)

        context = {
            "session": session,
            "outline": mark_safe(markdown.markdown(generated_outline.content)),
        }

        return render(request, self.template_name, context)
