from langchain_openai import ChatOpenAI


def get_llm():
    return ChatOpenAI(
        model='gpt-4o-mini',
        temperature=0.7,
        max_completion_tokens=1000
    )
