import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ai_support.ai_chain import (
    get_chat_model_for_question_generation,
    get_chat_model_for_report,
    get_chat_model_for_scoring,
    get_chat_model_for_summary,
)
from ai_support.modules.constraints.language_common import language_constraint_common
from ai_support.modules.constraints.common_system_messages import get_common_safety_rules

from exam.models import ExamSession

from ai_support.modules.exam.exam_history import (
    EvaluationHistoryBuilder,
    LearningStateSummaryUpdateHistoryBuilder,
    QuestionControlSummaryUpdateHistoryBuilder,
    QuestionGenerationHistoryBuilder,
    ReportHistoryBuilder,
)


# ========== Text Constants ==========
GLOBAL_PERSONAL = (
    "You are a standardized academic assessment system.\n"
    "Your role is to generate exam content, evaluate answers objectively, and produce structured reports.\n"
    "You must strictly follow all system rules and output format specifications."
)

JSON_RULES = (
    "JSON RULES:\n"
    "- The output will be a JSON object with the same structure as the example below.\n"
    "- The JSON structure must not be modified.\n"
    "- Do not include markdown.\n"
    "- Do not wrap the JSON in code blocks.\n"
    "- Do not include any text before or after the JSON.\n"
    "- Do not add or remove keys.\n"
    "- Do not change nesting levels."
    
)

# Target Rules
TARGET_SUB_TOPIC_STRICT_RULES = (
    "- The scope must be limited strictly to the current sub-topic.\n"
    "- Avoid covering multiple unrelated concepts."
)

TARGET_MAIN_TOPIC_STRICT_RULES = (
    "- The question may require integration of multiple sub-topics.\n"
    "- The task should require conceptual understanding, not memorization.\n"
    "- The question must cover one of the listed sub-topics.\n"
    "- Do not repeat previously used sub-topics if possible."

)

TARGET_LEARNING_GOAL_STRICT_RULES = (
    "- The task must require integration of multiple main topics.\n"
    "- The problem should simulate a realistic scenario."
)

# Exam Type Rules
MCQ_STRICT_RULES = (
    "STRICT RULES FOR MCQ GENERATION:\n"
    "- Generate a multiple choice question (MCQ) relevant to the current exam topic.\n"
    "- The question must have one correct answer and three plausible distractors.\n"
    "- Do not include any explanations or justifications in the question."
    "- The explanation must be concise (max 3 sentences).\n"
)

MCQ_OUTPUT_FORMAT_INSTRUCTION = (
    "OUTPUT FORMAT RULES:\n"
    f"{JSON_RULES}\n\n"
    "<example>\n"
    "{\n"
    '  "question": "...",\n'
    '  "choices": {\n'
    '    "A": "...",\n'
    '    "B": "...",\n'
    '    "C": "...",\n'
    '    "D": "..." \n'
    '  },\n'
    '  "answer": "A",\n'
    '  "explanation": "..."\n'
    "}"
)

# WT Generation Instructions
WT_STRICT_RULES = (
    "STRICT RULES FOR WRITTEN TASK GENERATION:\n"
    "- The questions should be centered around the 'current exam topic'.\n"
    "- The question should prompt for a detailed written response.\n"
    "- Do not include any specific formatting instructions for the answer."
)

def get_rubric_rules(session: ExamSession) -> str:
    rubric_schema = session.learning_goal.rubbic_schema
    return (
        "The evaluation must strictly follow the rubric below:\n"
        f"{rubric_schema}\n"
        "- Do not invent new items.\n"
        "- Do not change the maximum scores."
    )

def get_evaluation_strict_rules(session: ExamSession, max_score: int = 20) -> str:
    exam_type = session.exam_type.scoring_method
    if exam_type == "rubric":
        max_score = 20
    elif exam_type == "rubric_heavy":
        max_score = 100

    return (
        "EVALUATION STRICT RULES:\n"
        f"- It will be scored out of {max_score} points.\n"
        "- Provide a brief explanation justifying the score, highlighting key points from the student's answer that influenced the evaluation.\n"
        "- Evaluate only the student's answer. Do not generate new content.\n\n"
        f"{get_rubric_rules(session=session)}"
    )

EVALUATION_OUTPUT_FORMAT_INSTRUCTION = (
    "OUTPUT FORMAT RULES:\n"
    f"{JSON_RULES}\n\n"
    "<example>\n"
    "{\n"
    '  "total_score": 5.0,\n'
    '  "feedback": "...",\n'
    '  "detail_scores": {\n'
    '    "items": [\n'
    '      {\n'
    '        "key": "accuracy",\n'
    '        "score": 2.0,\n'
    '        "max_score": 3.0,\n'
    '        "evaluation": "..."\n'
    '      },\n'
    '      {\n'
    '        "key": "logic",\n'
    '        "score": 3.0,\n'
    '        "max_score": 3.0,\n'
    '        "evaluation": "..."\n'
    '      }\n'
    '    ]\n'
    "}"
)

# Summary Generation Instructions
SUMMARY_STRICT_RULES = (
    "STRICT RULES FOR SUMMARY GENERATION:\n"
    "- Generate a concise summary of the exam session so far, focusing on the questions generated and the flow of the exam.\n"
)


# ========== Generate Question ==========
# Exam Type: MCQ (Multiple Choice Question)
def generate_mcq_for_sub_topic(session: ExamSession) -> AIMessage:
    llm = get_chat_model_for_question_generation()
    history_builder = QuestionGenerationHistoryBuilder()
    history_messages = history_builder.build_messages(session=session)
    messages = [
        SystemMessage(content=(
            f"{GLOBAL_PERSONAL}\n"
            "You need to generate a multiple choice quiz on the current exam topic.\n\n"

            f"{language_constraint_common(user=session.user)}\n\n"

            "EXAM CONTEXT:\n"
            f"Learning Goal: {session.sub_topic.main_topic.learning_goal.title}\n"
            f"Main Topic: {session.sub_topic.main_topic.title}\n"
            f"Current Exam Topic: {session.sub_topic.title}\n\n"

            f"{MCQ_STRICT_RULES}\n"
            + f"{TARGET_SUB_TOPIC_STRICT_RULES}\n\n"

            f"{MCQ_OUTPUT_FORMAT_INSTRUCTION}"
        )),
        *history_messages,
        HumanMessage(content=(
            "Based on the above context and rules, generate the MCQ in the specified JSON format."
        ))
    ]
    response = llm.invoke(messages)
    return response

def generate_mcq_for_main_topic(session: ExamSession) -> AIMessage:
    all_sub_topics = session.main_topic.sub_topics.order_by("id")
    sub_topic_titles = [
         f"{i + 1}. {sub_topic.title}"
         for i, sub_topic in enumerate(all_sub_topics)
    ]

    llm = get_chat_model_for_question_generation()
    history_builder = QuestionGenerationHistoryBuilder()
    history_messages = history_builder.build_messages(session=session)
    messages = [
        SystemMessage(content=(
            f"{GLOBAL_PERSONAL}\n"
            "You need to generate a multiple choice quiz on the current exam topic.\n\n"

            f"{language_constraint_common(user=session.user)}\n\n"

            "EXAM CONTEXT:\n"
            f"Learning Goal: {session.main_topic.learning_goal.title}\n"
            f"Current Exam Topic: {session.main_topic.title}\n"
            f"All Sub-Topics:\n"
            + "\n".join(sub_topic_titles) + "\n\n"

            f"{MCQ_STRICT_RULES}\n"
            + f"{TARGET_MAIN_TOPIC_STRICT_RULES}\n\n"

            f"{MCQ_OUTPUT_FORMAT_INSTRUCTION}"
        )),
        *history_messages,
        HumanMessage(content=(
            "Based on the above context and rules, generate the MCQ in the specified JSON format."
        ))
    ]
    response = llm.invoke(messages)
    return response

# Exam Type: WT (Written Task)
def generate_wt_for_sub_topic(session: ExamSession) -> AIMessage:
    llm = get_chat_model_for_question_generation()
    messages = [
        SystemMessage(content=(
            f"{GLOBAL_PERSONAL}\n"
            "You need to generate a written task question on the current exam topic.\n\n"

            f"{language_constraint_common(user=session.user)}\n\n"

            "EXAM CONTEXT:\n"
            f"Learning Goal: {session.sub_topic.main_topic.learning_goal.title}\n"
            f"Main Topic: {session.sub_topic.main_topic.title}\n"
            f"Current Exam Topic: {session.sub_topic.title}\n\n"

            f"{WT_STRICT_RULES}\n"
            + f"{TARGET_SUB_TOPIC_STRICT_RULES}"
        )),
        HumanMessage(content=(
            "Based on the above context and rules, generate the written task question."
        ))
    ]
    response = llm.invoke(messages)
    return response

def generate_wt_for_main_topic(session: ExamSession) -> AIMessage:
    all_sub_topics = session.main_topic.sub_topics.order_by("id")
    sub_topic_titles = [
         f"{i + 1}. {sub_topic.title}"
         for i, sub_topic in enumerate(all_sub_topics)
    ]
    llm = get_chat_model_for_question_generation()
    history_builder = QuestionGenerationHistoryBuilder()
    history_messages = history_builder.build_messages(session=session)
    messages = [
        SystemMessage(content=(
            f"{GLOBAL_PERSONAL}\n"
            "You need to generate a written task question on the current exam topic.\n\n"

            f"{language_constraint_common(user=session.user)}\n\n"

            "EXAM CONTEXT:\n"
            f"Learning Goal: {session.main_topic.learning_goal.title}\n"
            f"Current Exam Topic: {session.main_topic.title}\n\n"
            f"All Sub-Topics:\n"
            + "\n".join(sub_topic_titles) + "\n\n"

            f"{WT_STRICT_RULES}\n"
            + f"{TARGET_MAIN_TOPIC_STRICT_RULES}"
        )),
        *history_messages,
        HumanMessage(content=(
            "Based on the above context and rules, generate the written task question."
        ))
    ]
    response = llm.invoke(messages)
    return response

# Exam Type: CT (Comprehensive Test)
def generate_ct_for_learning_goal(session: ExamSession) -> AIMessage:
    all_main_topics = session.learning_goal.main_topics.order_by("id")
    main_topic_titles = [
         f"{i + 1}. {main_topic.title}"
         for i, main_topic in enumerate(all_main_topics)
    ]
    llm = get_chat_model_for_question_generation()
    history_builder = QuestionGenerationHistoryBuilder()
    history_messages = history_builder.build_messages(session=session)
    messages = [
        SystemMessage(content=(
            f"{GLOBAL_PERSONAL}\n"
            "You need to generate a comprehensive test question on the current learning goal.\n\n"

            f"{language_constraint_common(user=session.user)}\n\n"

            "EXAM CONTEXT:\n"
            f"Learning Goal: {session.learning_goal.title}\n"
            f"All Main Topics:\n"
            + "\n".join(main_topic_titles) + "\n\n"

            "CT STRICT RULES:\n"
            "- The question should be comprehensive and cover multiple main topics under the learning goal.\n"
            "- The question should prompt for a detailed written response.\n"
            "- Do not include any specific formatting instructions for the answer.\n"
            + f"{TARGET_LEARNING_GOAL_STRICT_RULES}"
        )),
        HumanMessage(content=(
            "Based on the above context and rules, generate the comprehensive test question."
        ))
    ]
    response = llm.invoke(messages)
    return response


#========== Generate Evaluation ==========
# Scoring Method: rubric
def generate_rubric_evaluation(session: ExamSession) -> AIMessage:
    llm = get_chat_model_for_scoring()
    history_builder = EvaluationHistoryBuilder()
    history_messages = history_builder.build_messages(session=session)
    messages = [
        SystemMessage(content=(
            f"{GLOBAL_PERSONAL}\n"
            "You are an objective and strict exam evaluator.\n"
            "Evaluate the student's answer based on the question and provide a rubric-based score along with a brief explanation.\n\n"

            f"{language_constraint_common(user=session.user)}\n\n"

            f"{get_common_safety_rules()}\n\n"

            f"{get_evaluation_strict_rules(exam_type=session.exam_type.scoring_method)}\n\n"

            f"{EVALUATION_OUTPUT_FORMAT_INSTRUCTION}"
        )),
        *history_messages,
        HumanMessage(content=(
            "Based on the above context and rules, evaluate the student's answer and provide the score and explanation in the specified JSON format."
        ))
    ]
    response = llm.invoke(messages)
    return response

# Scoring Method: rubric heavy
def generate_heavy_rubric_evaluation(session: ExamSession) -> AIMessage:
    llm = get_chat_model_for_scoring()
    history_builder = EvaluationHistoryBuilder()
    history_messages = history_builder.build_messages(session=session)
    messages = [
        SystemMessage(content=(
            f"{GLOBAL_PERSONAL}\n"
            "You are an objective and strict exam evaluator.\n"
            "Evaluate the student's answer using the heavy rubric scoring system.\n\n"

            f"{language_constraint_common(user=session.user)}\n\n"

            f"{get_common_safety_rules()}\n\n"

            f"{get_evaluation_strict_rules(exam_type='rubric_heavy')}\n\n"

            f"{EVALUATION_OUTPUT_FORMAT_INSTRUCTION}"
        )),
        *history_messages,
        HumanMessage(content=(
            "Based on the above context and rules, evaluate the student's answer and provide the score and explanation in the specified JSON format."
        ))
    ]
    response = llm.invoke(messages)
    return response


# ========== Generate Summary ==========
# Usage: Flow type<batch>
def generate_question_control_summary(session: ExamSession) -> AIMessage:
    llm = get_chat_model_for_summary()
    history_builder = QuestionControlSummaryUpdateHistoryBuilder()
    history_messages = history_builder.build_messages(session=session)
    messages = [
        SystemMessage(content=(
            f"{GLOBAL_PERSONAL}\n"
            "You are an objective and strict exam summary generator.\n"

            f"{language_constraint_common(user=session.user)}\n\n"

            f"{SUMMARY_STRICT_RULES}"
        )),
        *history_messages,
        HumanMessage(content=(
            "Based on the above context and rules, generate the question control summary."
        ))
    ]
    response = llm.invoke(messages)
    return response

# Usage: Flow type<per question>, Report generation
def generate_learning_state_summary(session: ExamSession) -> AIMessage:
    llm = get_chat_model_for_summary()
    history_builder = LearningStateSummaryUpdateHistoryBuilder()
    history_messages = history_builder.build_messages(session=session)
    messages = [
        SystemMessage(content=(
            f"{GLOBAL_PERSONAL}\n"
            "You are an objective and strict exam summary generator.\n"

            f"{language_constraint_common(user=session.user)}\n\n"

            f"{SUMMARY_STRICT_RULES}"
        )),
        *history_messages,
        HumanMessage(content=(
            "Based on the above context and rules, generate the learning state summary."
        ))
    ]
    response = llm.invoke(messages)
    return response


# ========== Generate Report ==========
def generate_exam_report_for_report(session: ExamSession) -> AIMessage:
    llm = get_chat_model_for_report()
    history_builder = ReportHistoryBuilder()
    history_messages = history_builder.build_messages(session=session)
    messages = [
        SystemMessage(content=(
            f"{GLOBAL_PERSONAL}\n"
            "You are an objective and strict exam report generator.\n"
            "Generate a comprehensive report summarizing the student's performance in the exam session, including strengths, weaknesses, and actionable recommendations for improvement.\n\n"

            f"{language_constraint_common(user=session.user)}\n\n"

            "REPORT GENERATION STRICT RULES:\n"
            "- Provide a detailed analysis of the student's performance based on the questions and evaluations throughout the exam session.\n"
            "- Highlight specific strengths and weaknesses observed in the student's answers.\n"
            "- Offer actionable recommendations for improvement, tailored to the student's performance and learning goals."
        )),
        *history_messages,
        HumanMessage(content=(
            "Based on the above context and rules, generate the comprehensive exam report."
        ))
    ]
    response = llm.invoke(messages)
    return response
