import markdown
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.utils.safestring import mark_safe
from django.views import View, generic

from task_management.models import LearningMainTopic, LearningSubTopic

from exam.models import ExamAnswer, ExamEvaluation, ExamSession, ExamType
from exam.services import (
    create_new_exam_session,
    get_rubric_schema,
    get_exam_question,
    get_unanswered_question,
)


class ExamStartView(LoginRequiredMixin, View):
    def get(self, request, exam_type, topic_id):
        # Create a new exam session
        session = create_new_exam_session(user=request.user, exam_type=exam_type, topic_id=topic_id)
        context = {
            "session": session,
            "exam_type": session.exam_type,
            "current_topic_title": session.topic.title,
        }

        if session.exam_type.scoring_method == "rubric":
            rubric_schema = get_rubric_schema(session=session)
            context["rubric_schema"] = rubric_schema  

        return render(request, "exam/exam.html", context)


class ExamQuestionView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        session = get_object_or_404(ExamSession, id=session_id, user=request.user)
        if session.status != "in_progress":
            return render(request, "exam/exam.html", {"error": "Exam session is not active."})
        
        question = get_exam_question(session=session)
        if not question:
            return render(request, "exam/exam.html", {"error": "No more questions available."})
        
        html_content = mark_safe(markdown.markdown(question))
        context = {
            "question": html_content,
        }
        return JsonResponse(context)
        


class ExamSubmitView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        session = get_object_or_404(ExamSession, id=session_id, user=request.user)
        if session.status != "in_progress":
            return JsonResponse({"error": "Exam session is not active."}, status=400)
        
        answer = request.POST.get("answer", "").strip()
        question_obj = get_unanswered_question(session=session, answered=True)
        if not question_obj:
            return JsonResponse({"error": "No unanswered question found."}, status=400)
        ExamAnswer.objects.create(
            question=question_obj,
            answer=answer,
        )
        pass


class BatchExamNextView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        # Logic to handle answer submission and return results
        pass

class BatchExamEndView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        # Logic to finalize the exam and show results
        pass
