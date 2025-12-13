from abc import ABC, abstractmethod
from typing import List
from app_ai.domain.value_objects.retrieved_document import RetrievedDocument

class IRetriever(ABC):
    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[RetrievedDocument]:
        """根据查询词检索相关文档"""
        pass
