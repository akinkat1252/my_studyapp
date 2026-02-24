import json
import re

from accounts.models import CustomUser
from ai_support.ai_client import get_ai_client
from ai_support.modules.constraints.language_json import language_constraint_json
from ai_support.modules.task_management.validate import validate_learning_topic

client = get_ai_client()

def generate_learning_topic(title, current_level, target_level, description, user: CustomUser):
    prompt = (
        "Generate a detailed learning topic outline.\n\n"

        "LEARNING CONTEXT:\n"
        f"Title: {title}\n"
        f"Current Level: {current_level}\n"
        f"Target Level: {target_level}\n"
        f"Description: {description}\n\n"

        f"{language_constraint_json(user=user)}\n\n"

        "CONTENT RULES:\n"
        "- Divide the plan into main_topics and sub_topics.\n"
        "- Each sub_topic should take approximately 30-60 minutes of study.\n"
        "- Consider current_level and target_level if provided.\n"
        "- If optional inputs are empty, create a standard learning path.\n\n"

        "STRUCTURE RULES:\n"
        "- The JSON structure must not be modified.\n"
        "- Do not add or remove keys.\n"
        "- Do not change nesting levels.\n\n"

        "Required JSON structure:\n"
        "{\n"
        '  "main_topics": [\n'
        "    {\n"
        '      "title": string,\n'
        '      "sub_topics": [\n'
        '        {"title": string}\n'
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}"     
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert educational content creator."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    raw_ai_content = response.choices[0].message.content

    if not raw_ai_content:
        raise ValueError("AI response is empty.")

    try:
        parsed_json = json.loads(raw_ai_content)
    except json.JSONDecodeError:
        raise ValueError("AI returned invalid JSON despite strict mode.")
        
    validate_learning_topic(parsed_json)

    return parsed_json
