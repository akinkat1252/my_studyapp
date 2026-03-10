import markdown
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.views import View, generic

from task_management.models import LearningMainTopic, LearningSubTopic

from exam.models import ExamEvaluation, ExamSession, ExamType
from exam.services import (
    create_new_exam_session,
    get_rubric_schema
)


# Exam Type: Per Question (One question at a time)
class PerQuestionExamStartView(LoginRequiredMixin, View):
    def get(self, request, exam_type, topic_id):
        # Create a new exam session
        # session = create_new_exam_session(user=request.user, exam_type=exam_type, topic_id=topic_id)
        # if session.exam_type.scoring_method == "rubric":
        #     rubric_schema = get_rubric_schema(session=session)
        context = {
            "session": "session",  # Replace with actual session object
            "exam_type": "exam_type",  # Replace with actual exam type
            "current_topic_title": "Current Topic Title",  # Replace with actual topic title
        }
        context["rubric_schema"] = "rubric_schema"  # Replace with actual rubric schema if applicable

        return render(request, "exam/exam.html", context)

class PerQuestionExamNextView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        # Logic to handle answer submission and return next question
        pass

class PerQuestionExamEndView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        # Logic to finalize the exam and show results
        pass


# Exam Type: Batch (All questions at once)
class BatchExamStartView(LoginRequiredMixin, View):
    def get(self, request, exam_type, topic_id):
        # session = create_new_exam_session(user=request.user, exam_type=exam_type, topic=topic)
        context = {
            "session": "session",  # Replace with actual session object
            "exam_type": "exam_type",  # Replace with actual exam type
            "current_topic_title": "Current Topic Title",  # Replace with actual topic title
        }
        return render(request, "exam/exam.html", context)

class BatchExamNextView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        # Logic to handle answer submission and return results
        pass

class BatchExamEndView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        # Logic to finalize the exam and show results
        pass
