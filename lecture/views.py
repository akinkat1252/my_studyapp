import json
import markdown
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic, View
from django.urls import reverse
from django.utils.safestring import mark_safe
from datetime import datetime, timezone

from task_management.models import LearningMainTopic, LearningSubTopic
from .models import LectureSession, LectureLog, LectureTopic, LectureProgress
from .services import create_new_lecture_session
from ai_support.modules.lecture.generate_lecture import generate_lecture_outline
from .services import advance_lecture, handle_lecture_chat, finalize_lecture


# Create your views here.
class LectureStartView(LoginRequiredMixin, View):
    template_name = "lecture/lecture.html"

    def get(self, request, sub_topic_id):
        sub_topic = get_object_or_404(
            LearningSubTopic,
            user=self.request.user,
            id=sub_topic_id,
        )
        # Get previous session to reuse "lecture topic"
        outlines_qs = sub_topic.lecture_topics.all()

        if not outlines_qs.exists():
            # Generate lecture outline (response(AIMessage) -> [{"order": int, "title": str}...])
            ai_response = generate_lecture_outline(sub_topic=sub_topic)
            print(ai_response)
            generated_outline = json.loads(ai_response.content)

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

        next_lecture = advance_lecture(session=session) # {"is_ended": bool, "lecture_content": AIMessage}

        if next_lecture.get("is_ended"):
            return JsonResponse({"redirect_url": reverse("lecture:end_lecture", args=[session.id])})
        
        ai_response = next_lecture.get("lecture_content")
        html_content = mark_safe(markdown.markdown(ai_response.content))

        context = {
            "lecture_content": html_content,
        }

        return JsonResponse(context)


class LectureChatView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        session = get_object_or_404(
            LectureSession,
            id=session_id,
            user=request.user,
        )

        user_input = request.POST.get("user_input", "").strip()

        if not user_input:
            return JsonResponse({"error": "User input cannot be empty."}, status=400)
        
        ai_response = handle_lecture_chat(session=session, user_input=user_input)
        html_content = mark_safe(markdown.markdown(ai_response.content))

        context = {
            "lecture_content": html_content,
        }

        return JsonResponse(context)


class LectureEndView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        session = get_object_or_404(
            LectureSession,
            id=session_id,
            user=request.user,
        )

        finalize_lecture(session=session)

        return redirect("task_management:learning_goal_detail", goal_id=session.sub_topic.learning_goal.id)


class LectureReportView(LoginRequiredMixin, generic.DetailView):
    model = LectureSession
    template_name = "lecture/lecture_report.html"
    context_object_name = "session"

    def get_queryset(self):
        return LectureSession.objects.filter(user=self.request.user, id=self.kwargs['session_id'])
