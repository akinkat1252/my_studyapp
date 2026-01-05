def get_lecture_outline_prompt(sub_topic):
    prompt_text = (
       "You are a good teacher.Users will attend lectures on the following title.\n"
       f"Title: {sub_topic.title}\na"
       "Generate learning topics as an outline for delivering your lectures.\n"
       "The output must follow the rules below.\n"
       "1.First, output lecture topics as a numbered list.\n"
       "2.Each topic must be short and suitable as a section title.\n"
       "3.Output in the language used in the title.\n"
       "4.Output must be valid JSON (no extra text).\n"
       "<Example Output>\n"
       "[\n"
       '  {"order": 1, "title": "..."},\n'
       '  {"order": 2, "title": "..."},\n'
       "  ...\n"
       "]\n"
    )
    return prompt_text

def get_lecture_prompt(session, topic):
    prompt_text = (
       "You are a good teacher.Users will attend lectures on the following title.\n"
       f"Title: {session.sub_topic.title}\n"
       f"Current Topic: {topic.title}\n"
       "1.Deliver a lecture to the user based on the current topic.\n"
       "2.If you include examples such as programming code, they must be separated from the text.\n"
       "3.Provide clear and concise explanations, and engage the user with questions.\n"
    )
    return prompt_text
