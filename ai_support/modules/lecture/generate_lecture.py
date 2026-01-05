from ai_support.ai_chain import get_chat_model, invoke_llm
from lecture.models import LectureSession, LectureLog, LectureTopic, LectureProgress
from .lecture_history import LectureHistoryBuilder
from .lecture_prompts import get_lecture_outline_prompt, get_lecture_prompt


def generate_lecture_outline(sub_topic) -> dict:
    llm = get_chat_model()
    prompt = get_lecture_outline_prompt(sub_topic=sub_topic)
    response = llm.invoke(prompt)
    return response


def generate_lecture(session: LectureSession, topic: LectureTopic) -> str:
    llm = get_chat_model()
    prompt = get_lecture_prompt(session=session, topic=topic)
    response = llm.invoke(prompt)
    return response
