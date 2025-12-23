from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from ai_support.ai_history import BaseHistoryBuilder


class LectureHistoryBuilder(BaseHistoryBuilder):
    system_prompt = "You are an educational AI that gives lectures."

    ROLE_MAP = {
        "user": HumanMessage,
        "ai": AIMessage,
        "master": SystemMessage,
    }

    def _build_history(self, session):
        messages = []

        for log in session.logs.order_by("created_at"):
            msg_class = self.ROLE_MAP[log.role]
            messages.append(msg_class(content=log.message))

        return messages
