from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from abc import ABC, abstractmethod


class BaseHistoryBuilder:
    system_prompt = ""

    def build_message(self, session):
        messages = []

        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))

        messages.extend(self._build_history(session=session))
        return messages

    @abstractmethod
    def _build_history(self, session):
        pass
