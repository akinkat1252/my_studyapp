from abc import ABC, abstractmethod

from langchain_core.messages import BaseMessage, SystemMessage


class BaseHistoryBuilder(ABC):

    def build_messages(self, session) -> list[BaseMessage]:
        messages = []
        messages.extend(self.build_system_context(session=session))
        messages.extend(self.build_conversation(session=session))
        return messages

    @abstractmethod
    def build_system_context(self, session) -> list[SystemMessage]:
        pass

    @abstractmethod
    def build_conversation(self, session) -> list[BaseMessage]:
        pass
