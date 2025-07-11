from abc import ABC, abstractmethod
from pydantic import BaseModel


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate_response(self, prompt: str, response_schema=None) -> str:
        pass