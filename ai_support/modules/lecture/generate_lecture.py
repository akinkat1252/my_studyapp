import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ai_support.ai_chain import (
    get_chat_model_for_outline,
    get_chat_model_for_lecture,
    get_chat_model_for_summary,
    get_chat_model_for_report,
    )
from ai_support.modules.common.services import language_constraint, get_common_safety_rules
from lecture.models import (LectureLog, LectureProgress, LectureSession,
                            LectureTopic,
                            )

from task_management.models import LearningSubTopic

from .lecture_history import (LectureGenerationHistorybuilder,
                              LectureHistoryBuilder,
                              LectureReportHistoryBuilder,
                              LectureReportUpdateHistoryBuilder,
                              SummaryHistoryBuilder,
                              )


GLOBAL_PERSONAL = (
    "You are an educational AI that provides structured, clear instruction.\n"
    "You guide learners step by step and adapt explanations to their level."
)


def generate_lecture_outline(sub_topic: LearningSubTopic) -> AIMessage:
    llm = get_chat_model_for_outline()

    main_topic = sub_topic.main_topic
    all_sub_topics = main_topic.sub_topics.order_by("id")
    sub_topic_titles = [
        f"{i + 1}. {sub_topic.title}"
        for i, sub_topic in enumerate(all_sub_topics)
    ]

    messages = [
        SystemMessage(content=(
            f"{GLOBAL_PERSONAL}\n"
            "You are generating a lecture outline for ONE specific sub-topic.\n\n"

            f"{language_constraint(language=sub_topic.main_topic.user)}\n\n"

            "LECTURE STRUCTURE CONTEXT:\n"
            f"Learning Goal: {sub_topic.learning_goal.title}\n"
            f"Main Topic: {main_topic.title}\n\n"

            f"All sub-topics under this main topic:\n"
            + "\n".join(sub_topic_titles) + "\n\n"

            "CURRENT LECTURE TARGET:\n"
            f"- {sub_topic.title}\n\n"

            "STRICT RULES:\n"
            "- Generate an outline ONLY for the current lecture target.\n"
            "- Do NOT generate outlines for other sub-topics.\n"
            "- You may reference other sub-topics ONLY to provide context, not explanation.\n"
            "- Do NOT include content that belongs to previous or next sub-topics.\n\n"

            "OUTPUT FORMAT RULES:\n"
            "- Output a numbered lecture outline.\n"
            "- Each item must be short and suitable as a section title.\n"
            "- Output must be valid JSON only (no extra text).\n\n"

            "<Example Output>\n"
            "[\n"
            '  {"order": 1, "title": "..."},\n'
            '  {"order": 2, "title": "..."},\n'
            "]"
        )),
        HumanMessage(content="Generate the lecture outline."),
    ]
    response = llm.invoke(messages)
    try:
        data = json.loads(response.content)
    except json.JSONDecodeError:
        print(f"It is not JSON data:\n{response.content}")

    return response


def generate_lecture(session: LectureSession, topic: LectureTopic) -> AIMessage:
    llm = get_chat_model_for_lecture()
    history_builder = LectureGenerationHistorybuilder()
    history_messages = history_builder.build_messages(session=session)
    messages = [
        SystemMessage(content=(
            f"{GLOBAL_PERSONAL}\n\n"

            f"{language_constraint(language=session.user)}\n\n"

            "The output must follow the rules below.\n"
            "- There is no need to say hello or explain the next schedule.\n"
            "- Deliver a lecture to the user based on the current topic.\n"
            "- If you include examples such as programming code, they must be separated from the text.\n"
            "- Provide clear and concise explanations, and engage the user with questions."
        )),
        SystemMessage(content=(
            "You will need to deliver lectures on the following topics:\n"
            f"Learning Goal: {session.sub_topic.learning_goal.title}\n"
            f"Main lecture topic: {session.sub_topic.title}\n"
            f"Current lecture topic: {topic.title}"
        )),
        *history_messages,
        HumanMessage(content="Please generate the next lecture."),
    ]
    response = llm.invoke(messages)

    return response


def generate_lecture_summary(session: LectureSession) -> AIMessage:
    llm = get_chat_model_for_summary()
    history_builder = SummaryHistoryBuilder()
    history_messages = history_builder.build_messages(session=session)
    messages = [
        SystemMessage(content=(
            "You are an educational AI that maintains a running summary of a lecture.\n"
            "Update the existing summary using the new conversation.\n"
            "Preserve important past information. Never lose earlier content.\n\n"
            f"{language_constraint(language=session.user)}\n\n"
        )),
        *history_messages,
        HumanMessage(content="Please update the summary."),
    ]
    response = llm.invoke(messages)
    return response


def generate_lecture_answer(session: LectureSession, user_input: str) -> AIMessage:
    llm = get_chat_model_for_lecture()
    history_builder = LectureHistoryBuilder()
    history_messages = history_builder.build_messages(session=session)
    messages = [
        SystemMessage(content=(
            f"{GLOBAL_PERSONAL}\n"
            "Answer questions and guide the learner forward.\n\n"

            f"{get_common_safety_rules()}\n\n"

            f"{language_constraint(language=session.user)}\n\n"

            "Please respond based on the following rules.\n"
            "- Respond appropriately to the user's input while maintaining the context of the lecture.\n"
            "- If the user's response includes questions, answer them clearly and concisely.\n"
            "- Encourage further engagement and understanding of the topic."
        )),
        *history_messages,
        HumanMessage(content=(user_input)),
    ]
    response = llm.invoke(messages)
    return response


def generate_lecture_report(session: LectureSession) -> AIMessage:
    llm = get_chat_model_for_report()
    history_builder = LectureReportHistoryBuilder()
    history_messages = history_builder.build_messages(session=session)
    messages = [
        SystemMessage(content=(
            f"{GLOBAL_PERSONAL}\n\n"

            f"{language_constraint(language=session.user)}\n\n"

            "The output must follow the rules below.\n"
            "- Summarize what the student learned, what was covered, what remains unclear, and suggest next steps.\n"
            "- Highlight key points and important concepts covered during the lecture.\n"
            "- Suggest further reading or topics for the user to explore based on the lecture content.\n"
            "- Write it for the learner, not for the AI."
        )),
        SystemMessage(content=(
            f"Lecture Title: {session.sub_topic.title}\n"
        )),
        *history_messages,
        HumanMessage(content="Please generate a lecture report."),
    ]
    response = llm.invoke(messages)
    return response


def generate_update_report(session: LectureSession) -> AIMessage:
    llm = get_chat_model_for_report()
    history_builder = LectureReportUpdateHistoryBuilder()
    history_messages = history_builder.build_messages(session=session)
    messages = [
        SystemMessage(content=(
            f"{GLOBAL_PERSONAL}\n\n"

            f"{language_constraint(language=session.user)}\n\n"

            "The output must follow the rules below.\n"
            "- Update the existing report to reflect new content covered in the latest lecture segment.\n"
            "- Ensure the report remains coherent and comprehensive, integrating new information seamlessly.\n"
            "- Highlight any new key points or important concepts introduced during the latest lecture segment.\n"
            "- Suggest further reading or topics for the user to explore based on the updated lecture content.\n"
            "- Write it for the learner, not for the AI."
        )),
        SystemMessage(content=(
            f"Lecture Title: {session.sub_topic.title}\n"
        )),
        *history_messages,
        HumanMessage(content="Please update the lecture report."),
    ]
    response = llm.invoke(messages)
    return response
