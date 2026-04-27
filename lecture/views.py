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

from ai_support.modules.lecture.generate_lecture import generate_lecture_outline
from task_management.models import LearningMainTopic, LearningSubTopic

from lecture.models import (
    LectureLog,
    LectureProgress,
    LectureSession,
    LectureSessionSlice,
    LectureTopic,
)
from lecture.services import (
    advance_lecture,
    create_lecture_report,
    create_new_lecture_session,
    finalize_lecture,
    get_current_lecture_progress,
    handle_lecture_chat,
    update_lecture_report,
)


# Create your views here.
class LectureStartView(LoginRequiredMixin, View):
    template_name = "lecture/lecture.html"

    def get(self, request, sub_topic_id):
        sub_topic = get_object_or_404(
            LearningSubTopic,
            id=sub_topic_id,
            main_topic__user=request.user
        )

        # Ensure lecture topics exist for the sub-topic
        with transaction.atomic():
            outlines = list(
                LectureTopic.objects
                .select_for_update()
                .filter(sub_topic=sub_topic)
                .order_by("default_order")  
            )

            # Generate lecture topics if they do not exist
            if not outlines:
                ai_response = generate_lecture_outline(sub_topic=sub_topic)
                generated_outline = json.loads(ai_response.content)

                LectureTopic.objects.bulk_create([
                    LectureTopic(
                        sub_topic=sub_topic,
                        default_order=item["order"],
                        title=item["title"],
                    ) for item in generated_outline
                ])

                outlines = list(
                    LectureTopic.objects
                    .filter(sub_topic=sub_topic)
                    .order_by("default_order")
                )

        # Check for existing unfinished session
        last_session = (
            LectureSession.objects
            .filter(
                user=request.user,
                sub_topic=sub_topic,
                can_continue=True,
                is_finished=False,
            )
            .order_by("-id")
            .first()
        )
        if last_session:
            session = last_session
        else:
            # Create new session
            session = create_new_lecture_session(
                user=request.user,
                sub_topic=sub_topic
            )

        md_text = "\n".join(
            f"{outline.default_order}. {outline.title}" for outline in outlines
        )

        # Save the start time of the lecture
        LectureSessionSlice.objects.create(session=session)

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
            .order_by("id")
        )

        _display_time = 60

        # generate or update report as needed
        latest_log = session.logs.order_by("-id").last()

        if not session.report:
            lecture_report = create_lecture_report(session=session)
        elif latest_log and session.last_report_log_id != latest_log.id:
            lecture_report = update_lecture_report(session=session)
        else:
            next_progress = get_current_lecture_progress(session=session)
            lecture_report = {
                "generated_report": session.report,
                "used_tokens": session.used_tokens,
                "total_study_time_seconds": session.duration_seconds,
                "completed": True if not next_progress else False,
            }
        
        html_content = mark_safe(markdown.markdown(lecture_report["generated_report"]))

        context = {
            "session": session,
            "progresses": progresses,
            "report_content": html_content,
            "used_tokens": lecture_report["used_tokens"],
            "total_study_time_min": round(lecture_report["total_study_time_seconds"] / _display_time, 1),
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

        can_continue = request.POST.get("can_continue") is not None

        if can_continue:
            LectureSession.objects.filter(
                user=request.user,
                sub_topic=session.sub_topic,
                can_continue=True,
            ).exclude(id=session.id).update(can_continue=False)

            session.is_finished = False

        session.can_continue = can_continue
        session.save()

        return redirect("task_management:learning_goal_detail", goal_id=session.sub_topic.main_topic.learning_goal.id)
