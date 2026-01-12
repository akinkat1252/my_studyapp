from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from ai_support.ai_chain import get_chat_model_for_lecture, get_chat_model_for_summary
from lecture.models import LectureSession, LectureLog, LectureTopic, LectureProgress
from .lecture_history import SummaryHistoryBuilder, LectureHistoryBuilder


def generate_lecture_outline(sub_topic) -> dict:
    llm = get_chat_model_for_lecture()
    messages = [
        SystemMessage(content=(
            "You are a good teacher."
        )),
        SystemMessage(content=(
            "Users will attend lectures on the following title.\n"
            f"Title: {sub_topic.title}"
        )),
        SystemMessage(content=(
            "You need to generate learning topics that will serve as an outline for your lecture."
        )),
        SystemMessage(content=(
            "The output must follow the rules below.\n"
            "1.First, output lecture topics as a numbered list.\n"
            "2.Each topic must be short and suitable as a section title.\n"
            "3.Output in the language used in the title.\n"
            "4.Output must be valid JSON (no extra text)."
        )),
        SystemMessage(content=(
            "<Example Output>\n"
            "[\n"
            '  {"order": 1, "title": "..."},\n'
            '  {"order": 2, "title": "..."},\n'
            "  ...\n"
            "]\n"
        )),
        HumanMessage(content="Please generate the lecture outline."),
    ]
    response = llm.invoke(messages)
    return response


def generate_lecture(session: LectureSession, topic: LectureTopic) -> str:
    llm = get_chat_model_for_lecture()
    messages = [
        SystemMessage(content=(
            "You are an educational AI that gives lectures."
        )),
        SystemMessage(content=(
            f"Current topic: {topic.title}"
        )),
        SystemMessage(content=(
            f"Lecture summary so far:\n{session.summary}"
        )),
        SystemMessage(content=(
            "The output must follow the rules below.\n"
            "1.Deliver a lecture to the user based on the current topic.\n"
            "2.If you include examples such as programming code, they must be separated from the text.\n"
            "3.Provide clear and concise explanations, and engage the user with questions."
        )),
        HumanMessage(content="Please generate the next lecture."),
    ]
    response = llm.invoke(messages)
    return response


def generate_lecture_summary(session: LectureSession) -> str:
    llm = get_chat_model_for_summary()
    history_builder = SummaryHistoryBuilder()
    history = history_builder.build_messages(session=session)
    messages = [
        *history,
        HumanMessage(content="Please update the summary."),
    ]
    response = llm.invoke(messages)
    return response


def generate_lecture_chat(session: LectureSession, user_input: str) -> str:
    llm = get_chat_model_for_lecture()
    history_builder = LectureHistoryBuilder()
    history = history_builder.build_messages(session=session)
    messages = [
        SystemMessage(content=(
            "Please respond based on the following rules.\n"
            "1.Respond appropriately to the user's input while maintaining the context of the lecture.\n"
            "2.If the user's response includes questions, answer them clearly and concisely.\n"
            "3.Encourage further engagement and understanding of the topic."
        )),
        *history,
        HumanMessage(content=(user_input)),
    ]
    response = llm.invoke(messages)
    return response
