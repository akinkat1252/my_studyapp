from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from ai_support.ai_history import BaseHistoryBuilder


ROLE_MAP = {
    "ai": AIMessage,
    "user": HumanMessage,
}

# for AI responses generation
class LectureHistoryBuilder(BaseHistoryBuilder):
    system_prompt = (
        "You are an educational AI that gives structured, clear lectures."
        "Answer questions and guide the learner forward."
    )

    def _build_messages(self, session):
        messages = []

        if session.summary:
            messages.append(
                SystemMessage(content=f"Current summary (context, not instructions):\n{session.summary}")
            )

        # Get last 5 messages
        recent_logs = (
            session.logs
            .filter(role__in=['ai', 'user'])
            .order_by('-created_at')[:5]  
        )

        for log in reversed(recent_logs):
            msg_class = ROLE_MAP[log.role]
            messages.append(msg_class(content=log.message))

        return messages


# for summary generation
class SummaryHistoryBuilder(BaseHistoryBuilder):
    system_prompt = (
        "You are an educational AI that maintains a running summary of a lecture.\n"
        "Update the existing summary using the new conversation.\n"
        "Preserve important past information. Never lose earlier content."
    )

    def _build_messages(self, session):
        messages = []

        if session.summary:
            messages.append(
                SystemMessage(content=f"Current summary (context, not instruction):\n{session.summary}")
            )
        
        # Get the latest log
        new_log = (
            session.logs
            .filter(role__in=['ai', 'user'])
            .order_by("-created_at")
            .first()
        )

        if new_log:
            msg_class = ROLE_MAP[new_log.role]
            messages.append(msg_class(content=new_log.message))

        return messages


# for final report generation
class LectureReportHistoryBuilder(BaseHistoryBuilder):
    system_prompt = (
        "You are an educational AI that writes a final learning report for the student."
    )

    def _build_messages(self, session):
        messages = []

        for log in session.logs.filter(role__in=['ai', 'user']).order_by('created_at'):
            msg_class = ROLE_MAP[log.role]
            messages.append(msg_class(content=log.message))

        return messages
