# Multiple Choice Quiz (main_topic (=sub_topics))
def get_main_mcq_prompt(sub_topics: str) -> str:
    prompt_text = (
        'You are a good teacher, Please create one multiple-choice question about the following topics.\n'
        f'topics: {sub_topics}\n'
        'The output must follow the rules below.\n'
        '1.Avoid repeating or overly similar questions.\n'
        '2.Insert line breaks where necessary to make it easier to read.\n'
        '3.If you include examples such as programming code, they must be separated from the text.\n'
        '4.Please output in the language used by the user, such as the language used in the topics title.\n'
        '5.It only generates questions and answer choices.\n'
    )

    return prompt_text


# Multiple Choice Quiz (sub_topic)
def get_sub_mcq_prompt(sub_topic: str) -> str:
    prompt_text = (
        'You are a good teacher, Please create one multiple-choice question about the following topic.\n'
        f'topics: {sub_topic}\n'
        'The output must follow the rules below.\n'
        '1.Avoid repeating or overly similar questions.\n'
        '2.Insert line breaks where necessary to make it easier to read.\n'
        '3.If you include examples such as programming code, they must be separated from the text.\n'
        '4.Please output in the language used by the user, such as the language used in the topic title.\n'
        '5.It only generates questions and answer choices.\n'
    )

    return prompt_text


# Evaluation (mcq)
def get_mcq_evaluation_prompt(question: str, answer: str) -> str:
    prompt_text = (
        "Read the following question and answer choices and evaluate whether the user's answer is correct.\n"
        'Note: Be sure to carefully consider the correspondence between the option labels and their contents.\n'
        f'Question: {question}\n'
        f'Ansewer: {answer}\n'
        'The output must follow the rules below.\n'
        '1.Output must be valid JSON (no extra text).\n'
        '2.As in the example, divide it into score and explanation.\n'
        'example: {{"score": score, "explanation": explanation}}\n'
        '3.The score should be returned as a float type.\n'
        '4.A correct answer will be scored as 1 point, an incorrect answer will be scored as 0 points'
        '4.Please generate the explanation in the same language as the question.\n'
    )

    return prompt_text