from django.shortcuts import get_object_or_404

from accounts.models import CustomUser
from ai_support.modules.task_management.generate_rubric_schema import generate_rubric_schema
from exam.models import ExamType, ExamResult, ExamSession
from exam.exceptions import ExamTypeDomainError, ExamSessionStatusError
from task_management.models import LearningGoal, LearningMainTopic, LearningSubTopic


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


def get_exam_type(code: str) -> ExamType:
    return ExamType.objects.get_by_code(code)

def get_topic_object(user: CustomUser, exam_type: str, topic_id: int):
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


def create_new_exam_session(user, exam_type: str, topic_id: int) -> ExamSession:
    FIELD_MAP = {
        "goal": "learning_goal",
        "main": "main_topic",
        "sub": "sub_topic",
    }
    exam_type_obj = get_exam_type(code=exam_type)
    topic_obj = get_topic_object(user=user, exam_type=exam_type, topic_id=topic_id)

    field = FIELD_MAP.get(exam_type_obj.target_level)
    if not field:
        raise ExamTypeDomainError("Unsupported exam type.")
    
    session = ExamSession.objects.create(
        user=user,
        exam_type=exam_type_obj,
        **{field: topic_obj}
    )

    return session