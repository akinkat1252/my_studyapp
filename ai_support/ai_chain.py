from langchain_openai import ChatOpenAI


def get_chat_model():
    return ChatOpenAI(
        model='gpt-4o-mini',
        temperature=0.7,
        max_completion_tokens=1000
    )


def invoke_llm(messages):
    llm = get_chat_model()
    response = llm.invoke(messages)
    return response
