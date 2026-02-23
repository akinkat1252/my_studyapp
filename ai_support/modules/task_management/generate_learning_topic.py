import json
import re

from accounts.models import CustomUser
from ai_support.ai_client import get_ai_client
from ai_support.modules.common.services import language_constraint

client = get_ai_client()

def generate_learning_topic(title, current_level, target_level, description, user: CustomUser):
    prompt = (
        f"Generate a detailed learning topic outline for the following learning goal:\n"
        f"Title: {title}\n"
        f"Current Level: {current_level}\n"
        f"Target Level: {target_level}\n"
        f"Description: {description}\n\n"
        f"{language_constraint(user=user)}\n\n"
        f"The outline should include main topics and subtopics in a structured JSON format.\n"
        "<Creation Rules>\n"
        "1. Divide the plan into main topics and sub_topics, as shown in the example.\n"
        "2. Each sub_topic should take ~30-60 minutes of study.\n"
        "3. Current level and target level are optional but should be considered if provided.\n"
        "4. If optional inputs are empty, create the most standard learning path.\n"
        "5. Output must be valid JSON (no extra text).\n"
        "6. Output language should match the input language.\n\n"
        "<Example Output>\n"
        "{\n"
        '  "main_topics": [\n'
        "    {\n"
        '      "title": "Main Topic 1",\n'
        '      "sub_topics": [\n'
        "        {\"title\": \"Subtopic 1.1\"},\n"
        "        {\"title\": \"Subtopic 1.2\"}\n"
        "      ]\n"
        "    },\n"
        "    {\n"
        '      "title": "Main Topic 2",\n'
        '      "sub_topics": [\n'
        "        {\"title\": \"Subtopic 2.1\"},\n"
        "        {\"title\": \"Subtopic 2.2\"}\n"
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
        temperature=0.7,
    )
    print("AI Response:", response)

    raw_ai_content = response.choices[0].message.content.strip()
    json_text = raw_ai_content.replace("```json", "").replace("```", "").strip() 

    if not json_text:
        raise ValueError("AI response is empty.")

    try:
        parsed_json = json.loads(json_text)
    except json.JSONDecodeError:
        json_match = re.search(r'(\{.*\})', json_text, re.DOTALL)
        if json_match:
            try:
                parsed_json = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                raise ValueError("Failed to parse JSON from AI response.")

    return parsed_json
