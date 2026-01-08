import json
import markdown
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic, View
from django.urls import reverse
from django.utils.safestring import mark_safe

from task_management.models import LearningMainTopic, LearningSubTopic
from .models import LectureSession, LectureLog, LectureTopic, LectureProgress
from .services import create_new_lecture_session
from ai_support.modules.lecture.generate_lecture import (
    generate_lecture_outline, 
    generate_lecture,
    generate_lecture_summary,
    generate_lecture_chat,
)


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
        # check if the lecture has never started
        has_started = session.logs.filter(role='ai').exists()
        

        if not has_started:
            # Mark the previous topic as completed
            current_progress = (
                session.progress_records
                .filter(is_completed=False)
                .order_by("order")
                .first()
            )
            if current_progress:
                current_progress.is_completed = True
                current_progress.save()

        next_progress = (
            session.progress_records
            .filter(is_completed=False)
            .order_by("order")
            .first()
        )

        if not next_progress:
            return JsonResponse({"redirect_url": reverse("lecture:end_lecture", args=[session.id])})
        
        # generate lecture content
        ai_response = generate_lecture(session=session, topic=next_progress.topic)
        print(ai_response.content)

        # Log AI response
        usage = ai_response.usage_metadata or {}
        total_tokens = usage.get("total_tokens", 0)
        LectureLog.objects.create(
            session=session,
            role='ai',
            message=ai_response.content,
            token_count=total_tokens,
        )

        # generate summary and save to session
        summary_response = generate_lecture_summary(session=session)
        session.summary = summary_response.content
        session.save()

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
        
        # Log user input
        LectureLog.objects.create(
            session=session,
            role='user',
            message=user_input,
        )

        current_progress = (
            session.progress_records
            .filter(is_completed=False)
            .order_by("order")
            .first()
        )
        if not current_progress:
            return JsonResponse({"error": "No active lecture topic found."}, status=400)
        
        # generate lecture chat response
        ai_response = generate_lecture_chat(
            session=session,
            current_progress=current_progress,
            user_input=user_input,
        )
        print(ai_response.content)

        # Log AI response
        usage = ai_response.usage_metadata or {}
        total_tokens = usage.get("total_tokens", 0)
        LectureLog.objects.create(
            session=session,
            role='ai',
            message=ai_response.content,
            token_count=total_tokens,
        )

        
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
        pass