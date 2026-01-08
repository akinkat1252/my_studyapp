from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from ai_support.ai_history import BaseHistoryBuilder

# for AI responses generation
class LectureHistoryBuilder(BaseHistoryBuilder):
    system_prompt = "You are an educational AI that gives lectures."

    ROLE_MAP = {
        "ai": AIMessage,
        "user": HumanMessage,
        "system": SystemMessage,
    }

    def _build_history(self, session):
        messages = []

        if session.summary:
            messages.append(
                SystemMessage(content=f"Lecture Summary:\n{session.summary}")
            )
        recent_logs = (
            session.logs
            .exclude(role='system')
            .order_by('-created_at')[:5]  # Get last 5 messages
        )
        for log in reversed(recent_logs):
            msg_class = self.ROLE_MAP[log.role]
            messages.append(msg_class(content=log.message))

        return messages


# for summary generation
class SummaryHistoyBuilder(BaseHistoryBuilder):
    ROLE_MAP = {
        "ai": AIMessage,
        "user": HumanMessage,
        "system": SystemMessage,
    }

    def _build_history(self, session):
        messages = []

        recnet_logs = (
            session.logs
            .exclude(role='system')
            .order_by('-created_at')[:5]  # Get last 5 messages
        )

        for log in reversed(recnet_logs):
            msg_class = self.ROLE_MAP[log.role]
            messages.append(msg_class(content=log.message))

        return messages

        

