from errno import DomainError

from ai_support.modules.task_management.generate_rubric_schema import generate_rubric_schema
from exam.models import ExamResult, ExamSession


def get_result(session: ExamSession) -> ExamResult:
    if session.status != "finished":
        raise DomainError("Exam is not finalized.")
    return session.result


def resolve_rubric(session: ExamSession) -> str:
    if session.sub_topic and session.sub_topic.rubric_schema:
        return session.sub_topic.rubric_schema
    if session.main_topic and session.main_topic.rubric_schema:
        return session.main_topic.rubric_schema
    if session.learning_goal and session.learning_goal.rubric_schema:
        return session.learning_goal.default_rubric_schema
    return generate_rubric_schema(session=session)
