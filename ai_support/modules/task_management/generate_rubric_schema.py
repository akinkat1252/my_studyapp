import json
import re

from ai_support.ai_client import get_ai_client
from exam.models import ExamSession

client = get_ai_client()

def generate_rubric_schema(session: ExamSession, EXAM_CONTEXT="") -> dict:
    if session.learning_goal:
        EXAM_CONTEXT = (

        )
    if session.main_topic:
        EXAM_CONTEXT = (

        )
    if session.sub_topic:
        EXAM_CONTEXT = (

        )
    
    prompt = (
        "The user set the following learning objectives and registered the following learning tasks.\n"

    )