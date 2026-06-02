import os
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

class GeminiVisionLLM:
    def __init__(self, model_name="models/gemini-2.5-flash"): # <-- AQUÍ ESTÁ LA MAGIA
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(model_name)
        else:
            print("ERROR: No se encontró la variable GEMINI_API_KEY")

    def load_model(self):
        if not self.api_key:
            raise ValueError("Falta la API Key de Gemini")
        print("--- Conectado a Google Gemini API (v1) ---")

    def process_image(self, image, prompt):
        try:
            # Quitamos el generation_config que daba error
            response = self.model.generate_content([prompt, image])
            
            text = response.text
            
            # Limpiamos la respuesta para quedarnos solo con el JSON
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "{" in text:
                text = text[text.find("{"):text.rfind("}")+1]
            
            return text
        except Exception as e:
            return f"{{\"error\": \"Error en Gemini: {str(e)}\"}}"