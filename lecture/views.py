import json
import markdown
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic, View
from django.utils.safestring import mark_safe

from task_management.models import LearningMainTopic, LearningSubTopic
from .models import LectureSession, LectureLog, LectureTopic
from .services import create_new_lecture_session
from ai_support.modules.lecture.generate_lecture import generate_lecture_outline


# Create your views here.
class LectureStartView(LoginRequiredMixin, View):
    template_name = "lecture/lecture.html"

    def get(self, request, topic_id):
        sub_topic = get_object_or_404(
            LearningSubTopic,
            user=self.request.user,
            id=topic_id,
        )
        # Get previous session to reuse "lecture topic"
        outlines_qs = sub_topic.lecture_topics.all()

        if not outlines_qs.exists():
            # Generate lecture outline (response(AIMessage) -> [{"order": int, "title": str}...])
            response = generate_lecture_outline(sub_topic=sub_topic)
            generated_outline = json.loads(response.content)

            try:
                with transaction.atomic():
                    if not LectureTopic.objects.filter(sub_topic=sub_topic).exists():
                        for item in generated_outline:
                            LectureTopic.objects.create(
                                sub_topic=sub_topic,
                                default_order=item['order'],
                                title=item['title'],
                            )
            except IntegrityError:
                pass

            outlines_qs = sub_topic.lecture_topics.all().order_by("default_order")

        # Create new session
        session = create_new_lecture_session(user=request.user, sub_topic=sub_topic)

        md_text = "\n".join(
            f"{outline.default_order}. {outline.title}" for outline in outlines_qs
        )

        context = {
            "session": session,
            "outline": mark_safe(markdown.markdown(md_text)),
        }

        return render(request, self.template_name, context)


class LectureNextView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        session = get_object_or_404(
            LectureSession,
            id=session_id,
            user=request.user,
        )
        pass


class LectureChatView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        session = get_object_or_404(
            LectureSession,
            id=session_id,
            user=request.user,
        )
        pass


class LectureEndView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        session = get_object_or_404(
            LectureSession,
            id=session_id,
            user=request.user,
        )
        pass