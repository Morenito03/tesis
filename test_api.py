import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"Llave encontrada: {'Sí' if api_key else 'No'}")

try:
    genai.configure(api_key=api_key)
    print("Modelos disponibles para ti:")
    
    # Esto le pregunta directamente a Google a qué modelos tienes derecho a acceder
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
            
except Exception as e:
    print("Error de conexión o bloqueo:", e)