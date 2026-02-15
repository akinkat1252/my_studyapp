from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai.chat_models import ChatOpenAI

from ai_support.ai_chain import get_chat_model_for_lecture, invoke_llm
from ai_support.modules.common.services import language_constraint, get_common_safety_rules


llm = get_chat_model_for_lecture()

