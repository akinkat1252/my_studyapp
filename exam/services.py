from errno import DomainError

from exam.models import ExamResult, ExamSession


def get_result(session: ExamSession) -> ExamResult:
    if session.status != "finished":
        raise DomainError("Exam is not finalized.")
    return session.result
