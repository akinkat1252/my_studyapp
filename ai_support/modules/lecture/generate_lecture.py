from ai_support.ai_chain import get_chat_model_for_lecture, get_chat_model_for_summary
from lecture.models import LectureSession, LectureLog, LectureTopic, LectureProgress
from .lecture_history import SummaryHistoyBuilder, LectureHistoryBuilder
from .lecture_prompts import (
    get_lecture_outline_prompt,
    get_lecture_prompt,
    get_summary_prompt,
    get_lecture_chat_prompt,
)

def generate_lecture_outline(sub_topic) -> dict:
    llm = get_chat_model_for_lecture()
    prompt = get_lecture_outline_prompt(sub_topic=sub_topic)
    response = llm.invoke(prompt)
    return response

def generate_lecture(session: LectureSession, topic: LectureTopic) -> str:
    llm = get_chat_model_for_lecture()
    prompt = get_lecture_prompt(session=session, topic=topic)
    response = llm.invoke(prompt)
    return response

def generate_lecture_summary(session: LectureSession) -> str:
    llm = get_chat_model_for_summary()
    history_builder = SummaryHistoyBuilder()
    history = history_builder.build_message(session=session)
    prompt = get_summary_prompt(history=history)
    response = llm.invoke(prompt)
    return response

def generate_lecture_chat(session: LectureSession, current_progress: LectureProgress, user_input: str) -> str:
    llm = get_chat_model_for_lecture()
    history_builder = LectureHistoryBuilder()
    history = history_builder.build_message(session=session)
    prompt = get_lecture_chat_prompt(session=session, current_progress=current_progress, history=history, user_input=user_input)
    response = llm.invoke(prompt)
    return response
