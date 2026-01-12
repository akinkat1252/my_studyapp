from langchain_core.messages import HumanMessage, AIMessage
from ai_support.ai_history import BaseHistoryBuilder


class ExamHistoryBuilder(BaseHistoryBuilder):
    system_prompt = "You are an AI that creates exam questions."

    def _build_messages(self, session):
        messages = []

        for log in session.logs.order_by("question_number"):
            messages.append(AIMessage(content=log.question))

            if log.answer:
                messages.append(HumanMessage(content=log.answer))

        return messages
