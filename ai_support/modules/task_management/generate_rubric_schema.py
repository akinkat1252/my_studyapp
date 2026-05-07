import json
import re

from ai_support.ai_client import get_ai_client
from exam.models import ExamSession
from ai_support.modules.task_management.validate import validate_rubric_schema

client = get_ai_client()

def generate_rubric_schema(session: ExamSession, EXAM_CONTEXT="", TOPIC_RULES="", max_score=100) -> dict:
    if session.learning_goal:
        all_main_topics = session.learning_goal.main_topics.order_by("id")
        main_topic_titles = [
            f"{i+1}. {main_topic.title}"
            for i, main_topic in enumerate(all_main_topics)
        ]

        EXAM_CONTEXT = (
            f"Learning Goal: {session.learning_goal.title}\n"
            f"ALL Main-Topics: {main_topic_titles}"
        )

        TOPIC_RULES = (
            "- The rubric must assess integration across multiple main topics.\n"
            "- Criteria should reward cross-topic reasoning rather than isolated knowledge.\n"
            "- Include at least one criterion specifically evaluating integrative thinking."
        )


    if session.main_topic:
        max_score = 20
        all_sub_topics = session.main_topic.sub_topics.order_by("id")
        sub_topic_titles = [
            f"{i+1}. {sub_topic.title}"
            for i, sub_topic in enumerate(all_sub_topics)
        ]
        EXAM_CONTEXT = (
            f"Learning Goal: {session.main_topic.learning_goal.title}\n"
            f"Exam Topic: {session.main_topic.title}\n"
            f"All Sub-Topics: {sub_topic_titles}"
        )

        TOPIC_RULES = (
            "- The rubric must assess conceptual understanding across relevant subtopics.\n"
            "- At least one criterion must evaluate application of concepts.\n"
            "- Pure memorization-based criteria are not allowed."
        )

    if session.sub_topic:
        max_score = 20
        EXAM_CONTEXT = (
            f"Learning Goal: {session.sub_topic.main_topic.learning_goal.title}\n"
            f"Main Topic: {session.sub_topic.main_topic.title}\n"
            f"Current Exam Topic: {session.sub_topic.title}"
        )
        TOPIC_RULES = (
            "- The rubric must strictly evaluate only the current subtopic.\n"
            "- Criteria should assess depth of understanding and precise conceptual clarity.\n"
            "- Do not include criteria that depend on other topics."
        )

    prompt = (
        "You are a standardized academic assessment designer.\n"
        "Your task is to generate a scoring rubric schema (NOT a scored result).\n"

        "EXAM_CONTEXT:\n"
        f"{EXAM_CONTEXT}\n\n"

        "TOPIC_RULES:\n"
        f"{TOPIC_RULES}\n\n"

        "RUBRIC_SPECIFICATIONS:\n"
        "- Include 3 to 6 distinct, non-overlapping criteria.\n"
        "- Each criterion must include:\n"
        "   - key (snake_case string)\n"
        "   - description (clear and academically precise explanation)\n"
        "   - max_score (float or integer)\n"
        f"- The sum of all max_score values must equal {max_score}.\n"
        "- This is a rubric schema only; do not generate any evaluation result.\n\n"

        "SCORING_DESIGN_RULES:\n"
        "- Score distribution must reflect cognitive complexity and importance.\n"
        "- Avoid mechanically equal score allocation unless pedagogically justified.\n\n"

        "STRUCTURE_REFERENCE:\n"
        "{\n"
        '  "max_total_score": <number>,\n'
        '  "criteria": [\n'
        '    {\n'
        '      "key": "<snake_case_identifier>",\n'
        '      "description": "<academic explanation>",\n'
        '      "max_score": <number>\n'
        '    }\n'
        '  ]\n'
        '}\n'
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert educational content creator."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    
    raw_ai_content = response.choices[0].message.content

    if not raw_ai_content:
        raise ValueError("AI response is empty.")
    
    try:
        parsed_json = json.loads(raw_ai_content)
    except json.JSONDecodeError:
        raise ValueError("AI returned invalid JSON despite strict mode.")
            
    validate_rubric_schema(parsed_json)

    return parsed_json
