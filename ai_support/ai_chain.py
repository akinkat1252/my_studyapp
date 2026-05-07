from langchain_openai import ChatOpenAI


def get_chat_model_for_outline():
    return ChatOpenAI(
        model='gpt-4o-mini',
        temperature=0.3,
        max_completion_tokens=1000
    )

def get_chat_model_for_lecture():
    return ChatOpenAI(
        model='gpt-4o-mini',
        temperature=0.45,
        max_completion_tokens=1000
    )

def get_chat_model_for_summary():
    return ChatOpenAI(
        model='gpt-4o-mini',
        temperature=0.1,
        max_completion_tokens=500
    )

def get_chat_model_for_report():
    return ChatOpenAI(
        model='gpt-4o-mini',
        temperature=0.3,
        max_completion_tokens=1000
    )

def get_chat_model_for_question_generation():
    return ChatOpenAI(
        model='gpt-4o-mini',
        temperature=0.3,
        max_completion_tokens=1000
    )

def get_chat_model_for_scoring():
    return ChatOpenAI(
        model='gpt-4o-mini',
        temperature=0.1,
        max_completion_tokens=500
    )
