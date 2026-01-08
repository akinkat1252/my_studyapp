from langchain_openai import ChatOpenAI


def get_chat_model_for_lecture():
    return ChatOpenAI(
        model='gpt-4o-mini',
        temperature=0.7,
        max_completion_tokens=1000
    )

def get_chat_model_for_summary():
    return ChatOpenAI(
        model='gpt-4o-mini',
        temperature=0.3,
        max_completion_tokens=500
    )
