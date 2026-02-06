import markdown
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.views import View, generic

from task_management.models import LearningMainTopic, LearningSubTopic

from .models import ExamEvaluation, ExamSession


# Create your views here.
class MultipleChoiceQuizView(LoginRequiredMixin, View):
    template_name = "exam/exam.html"
    format_text = "Multiple Choice Quiz"

    def get(self, request, topic_id):
        url_name = request.resolver_match.url_name

        if "main" in url_name:
            topic_obj = get_object_or_404(
                LearningMainTopic,
                user=request.user,
                id=topic_id,
            )
            topic_filter = {"main_topic": topic_obj}
        elif "sub" in url_name:
            topic_obj = get_object_or_404(
                LearningSubTopic,
                user=request.user,
                id=topic_id,
            )
            topic_filter = {"sub_topic": topic_obj}
        else:
            raise ValueError("The URL name does not contain 'main' or 'sub''.")
        

        context = {
            "format": self.format_text,
            "title": topic_obj.title,
        }

        return render(request, self.template_name, context)