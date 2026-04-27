import json
from django.shortcuts import get_object_or_404

from accounts.models import CustomUser
from ai_support.modules.task_management.generate_rubric_schema import generate_rubric_schema
from ai_support.modules.exam.generate_exam import (
    generate_mcq_for_main_topic,
    generate_mcq_for_sub_topic,
    generate_wt_for_main_topic,
    generate_wt_for_sub_topic,
    generate_ct_for_learning_goal,
)
from exam.validate import validate_mcq_question
from exam.models import ExamType, ExamResult, ExamSession, ExamQuestion, ExamAnswer, ExamEvaluation
from exam.exceptions import ExamTypeDomainError, ExamSessionStatusError
from task_management.models import LearningGoal, LearningMainTopic, LearningSubTopic


def _get_exam_type(code: str) -> ExamType:
    return ExamType.objects.get_by_code(code)


def _get_topic_object(user: CustomUser, exam_type: str, topic_id: int):
    if exam_type.endswith("_main"):
        return get_object_or_404(
            LearningMainTopic, 
            user=user,
            id=topic_id
        )
    elif exam_type.endswith("_sub"):
        return get_object_or_404(
            LearningSubTopic, 
            user=user,
            id=topic_id
        )
    elif exam_type.endswith("_goal"):
        return get_object_or_404(
            LearningGoal, 
            user=user,
            id=topic_id
        )
    else:
        raise ExamTypeDomainError("Invalid exam type.")


def get_result(session: ExamSession) -> ExamResult:
    if session.status != "finished":
        raise ExamSessionStatusError("Exam is not finalized.")
    return session.result


def get_rubric_schema(session: ExamSession) -> dict:
    if session.target.rubric_schema:
        return session.target.rubric_schema
    rubric_schema = generate_rubric_schema(session=session)
    session.target.rubric_schema = rubric_schema
    session.target.save(update_fields=["rubric_schema"])
    return rubric_schema


def create_new_exam_session(user, exam_type: str, topic_id: int) -> ExamSession:
    FIELD_MAP = {
        "goal": "learning_goal",
        "main": "main_topic",
        "sub": "sub_topic",
    }
    exam_type_obj = _get_exam_type(code=exam_type)
    topic_obj = _get_topic_object(user=user, exam_type=exam_type, topic_id=topic_id)

    field = FIELD_MAP.get(exam_type_obj.target_level)
    if not field:
        raise ExamTypeDomainError("Unsupported exam type.")
    
    session = ExamSession.objects.create(
        user=user,
        exam_type=exam_type_obj,
        **{field: topic_obj}
    )
    return session


class ExamQuestion:
    def get_question(self, session: ExamSession):
        if session.exam_type.code == "mcq_main":
            return generate_mcq_for_main_topic(session=session)
        elif session.exam_type.code == "mcq_sub":
            return generate_mcq_for_sub_topic(session=session)
        elif session.exam_type.code == "wt_main":
            return generate_wt_for_main_topic(session=session)
        elif session.exam_type.code == "wt_sub":
            return generate_wt_for_sub_topic(session=session)
        elif session.exam_type.code == "ct_goal":
            return generate_ct_for_learning_goal(session=session)
        else:
            raise ExamTypeDomainError("Unsupported exam type.")
        

def get_unanswered_question(session: ExamSession, answered: bool = False) -> ExamQuestion:
    question_obj = session.questions.filter(status="generated").order_by("created_at").first()
    if answered and question_obj:
        question_obj.status = "answered"
        question_obj.save(update_fields=["status"])
    return question_obj.question if question_obj else None


def get_exam_question(session: ExamSession) -> str:
    # Check if there's an already generated but unanswered question
    question = get_unanswered_question(session=session)
    if question:
        return question
    
    # If not, generate a new question
    question_generator = ExamQuestion()
    ai_response = question_generator.get_question(session=session)
    if session.exam_type == "mcq_main" or session.exam_type.code == "mcq_sub":
        validate_mcq_question(ai_response)

    # Extract token usage if available
    usage = ai_response.usage_metadata or {}
    total_tokens = usage.get("total_tokens", 0)

    # Save Log
    if session.exam_type.code == "mcq_main" or session.exam_type.code == "mcq_sub":
        generated_question = json.loads(ai_response.content)
        ExamQuestion.objects.create(
            session=session,
            status="generated",
            question=generated_question["question"],
            choices=generated_question["choices"],
            correct_answer=generated_question["correct_answer"],
            explanation=generated_question["explanation"],
            max_score=session.exam_type.max_score_per_question,
            token_count=total_tokens,
        )
        return generated_question["question"]
    
    ExamQuestion.objects.create(
        session=session,
        status="generated",
        question=ai_response.content,
        max_score=session.exam_type.max_score_per_question,
        token_count=total_tokens,
    )    
    return ai_response.content


def evaluate_answer(question: ExamQuestion, user_answer: str) -> ExamEvaluation:
    
    # Placeholder for evaluation logic, which could involve AI or predefined rules
    if question.session.exam_type.code.startswith("mcq"):
        is_correct = user_answer.strip().lower() == question.correct_answer.strip().lower()
        score = question.max_score if is_correct else 0
        feedback = "Correct!" if is_correct else f"Incorrect. The correct answer is: {question.correct_answer}"
    else:
        # For non-MCQ types, we might use AI to evaluate the answer
        score = 0  # Placeholder for actual scoring logic
        feedback = "Your answer has been submitted for evaluation."

    evaluation = ExamEvaluation.objects.create(
        question=question,
        user_answer=user_answer,
        score=score,
        feedback=feedback,
    )
    return evaluation