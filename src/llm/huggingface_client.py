import os
import requests
import base64
from io import BytesIO
from dotenv import load_dotenv # <-- 1. Añadimos esto

load_dotenv() # <-- 2. Esto obliga a Python a leer tu archivo .env

class HuggingFaceVisionLLM:
    def __init__(self, model_id="meta-llama/Llama-3.2-11B-Vision-Instruct"):
        self.model_id = model_id
        self.api_url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
        self.api_token = os.getenv("HF_TOKEN")
        
        # 3. Un pequeño chivato visual en tu consola para saber si leyó la llave:
        if self.api_token:
            print(f"Llave detectada: {self.api_token[:5]}***")
        else:
            print("¡PELIGRO! No se encontró el HF_TOKEN en el .env")

    def load_model(self):
        # En modo API no hace falta cargar nada local, solo verificar token
        if not self.api_token:
            raise ValueError("No se encontró HF_TOKEN en las variables de entorno.")
        print(f"--- Conectado a Hugging Face API: {self.model_id} ---")

    def process_image(self, image, prompt, system_prompt=None):
        # Convertir imagen PIL a base64 para enviarla por internet
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        payload = {
            "inputs": {
                "image": img_str,
                "question": prompt
            }
        }

        response = requests.post(self.api_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            return {"error": f"Error de API: {response.text}"}
            
        return response.json()