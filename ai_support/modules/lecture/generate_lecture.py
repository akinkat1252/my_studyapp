from ai_support.ai_chain import get_chat_model, invoke_llm
from lecture.models import LectureSession, LectureLog
from .lecture_history import LectureHistoryBuilder
from .lecture_prompts import get_lecture_outline_prompt


def generate_lecture_outline(session: LectureSession) -> dict:
    llm = get_chat_model()
    prompt = get_lecture_outline_prompt(session=session)
    response = llm.invoke(prompt)
    return response

