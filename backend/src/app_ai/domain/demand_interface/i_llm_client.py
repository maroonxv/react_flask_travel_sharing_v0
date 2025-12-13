from abc import ABC, abstractmethod
from typing import List, Generator
from app_ai.domain.entity.ai_message import AiMessage

class ILlmClient(ABC):
    @abstractmethod
    def stream_chat(self, messages: List[AiMessage], system_prompt: str) -> Generator[str, None, None]:
        """流式对话"""
        pass
        
    @abstractmethod
    def chat(self, messages: List[AiMessage], system_prompt: str) -> str:
        """普通对话"""
        pass
