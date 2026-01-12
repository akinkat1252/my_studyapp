from langchain_core.messages import SystemMessage
from abc import ABC, abstractmethod


class BaseHistoryBuilder:
    system_prompt: str = ""

    def build_messages(self, session) -> list:
        messages = []

        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))

        messages.extend(self._build_messages(session=session))
        return messages

    @abstractmethod
    def _build_messages(self, session) -> list:
        pass
