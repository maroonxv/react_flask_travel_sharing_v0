import os
from typing import List, Generator
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage as LangChainAIMessage
from app_ai.domain.demand_interface.i_llm_client import ILlmClient
from app_ai.domain.entity.ai_message import AiMessage

class LangChainDeepSeekAdapter(ILlmClient):
    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        
        if not api_key:
            # Fallback for dev/test without key, or raise error
            print("Warning: DEEPSEEK_API_KEY not found.")
            self.llm = None
        else:
            self.llm = ChatOpenAI(
                model="deepseek-chat",
                api_key=api_key,
                base_url=base_url,
                streaming=True
            )
            
    def _convert_messages(self, messages: List[AiMessage], system_prompt: str):
        lc_messages = [SystemMessage(content=system_prompt)]
        for msg in messages:
            if msg.role == 'user':
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == 'assistant':
                lc_messages.append(LangChainAIMessage(content=msg.content))
        return lc_messages

    def stream_chat(self, messages: List[AiMessage], system_prompt: str) -> Generator[str, None, None]:
        if not self.llm:
            yield "Error: LLM not configured."
            return

        lc_messages = self._convert_messages(messages, system_prompt)
        
        try:
            for chunk in self.llm.stream(lc_messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            yield f"Error calling LLM: {str(e)}"

    def chat(self, messages: List[AiMessage], system_prompt: str) -> str:
        if not self.llm:
            return "Error: LLM not configured."
            
        lc_messages = self._convert_messages(messages, system_prompt)
        response = self.llm.invoke(lc_messages)
        return response.content
