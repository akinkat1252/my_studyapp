import json
from datetime import datetime, timezone

import markdown
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views import View, generic

from ai_support.modules.lecture.generate_lecture import \
    generate_lecture_outline
from task_management.models import LearningMainTopic, LearningSubTopic

from .models import LectureLog, LectureProgress, LectureSession, LectureTopic
from .services import (advance_lecture, create_lecture_report,
                       create_new_lecture_session, finalize_lecture,
                       get_current_lecture_progress, handle_lecture_chat)


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
            "current_topic_title": next_lecture.get("current_topic").title,
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

        return redirect("lecture:lecture_report", session_id=session.id)


class LectureReportView(LoginRequiredMixin, View):
    def get(self, request, session_id):
        session = get_object_or_404(
            LectureSession,
            id=session_id,
            user=request.user,
        )
        progresses = (
            LectureProgress.objects
            .select_related("topic")
            .filter(session=session)
            .order_by("order")
        )

        _display_time = 60

        if not session.report:
            lecture_report = create_lecture_report(session=session)
        else:
            next_progress = get_current_lecture_progress(session=session)
            lecture_report = {
                "generated_report": session.report,
                "total_tokens": session.total_tokens,
                "study_time_seconds": session.duration_seconds,
                "completed": True if not next_progress else False,
            }
        
        html_content = mark_safe(markdown.markdown(lecture_report["generated_report"]))

        context = {
            "session": session,
            "progresses": progresses,
            "report_content": html_content,
            "total_tokens": lecture_report["total_tokens"],
            "study_time_min": lecture_report["study_time_seconds"] / _display_time,
            "completed": lecture_report["completed"],
        }
        return render(request, "lecture/lecture_report.html", context)

class LectureFinishView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        session = get_object_or_404(
            LectureSession,
            id=session_id,
            user=request.user,
        )
