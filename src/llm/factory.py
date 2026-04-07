import os
from src.llm.moondream import MoondreamLLM
from src.llm.qwen2vl import Qwen2VL

class LLMFactory:
    @staticmethod
    def create():
        model_type = os.getenv("LLM_MODEL_TYPE", "local")
        model_name = os.getenv("OLLAMA_MODEL", "vikhyatk/moondream2")

        # Si el tipo NO es ollama, usamos tus clases de la carpeta /llm
        if "moondream" in model_name.lower():
            print("--- Usando Moondream desde Hugging Face ---")
            return MoondreamLLM(
                model_name=model_name,
                device="cpu" # Importante: tu i7 no tiene CUDA
            )
        
        if "qwen" in model_name.lower():
            print("--- Usando Qwen2-VL desde Hugging Face ---")
            return Qwen2VL(
                model_name=model_name,
                device="cpu"
            )

        raise ValueError(f"Modelo no reconocido para carga local: {model_name}")