import os
from src.llm.gemini_client import GeminiVisionLLM

class LLMFactory:
    @staticmethod
    def create():
        model_type = os.getenv("LLM_MODEL_TYPE", "gemini")
        
        if model_type == "gemini":
            return GeminiVisionLLM()
        # ... resto de opciones