import time
import io
import os
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

# Importación absoluta desde tu carpeta src
from src.llm.factory import LLMFactory

app = FastAPI(title="Medistruct Single-IA Service")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variable global para mantener el modelo en RAM (i7 3ra Gen / 8GB RAM)
vision_llm = None

@app.post("/process") # Mantenemos /process para evitar el 404 en tu React
async def process_image_all_in_one(
    image: UploadFile = File(...),
    user_id: str = Form("default_user"),
    timestamp: str = Form("now")
):
    global vision_llm

    # 1. Cargar el modelo solo la primera vez
    if vision_llm is None:
        try:
            print("--- Cargando modelo desde LLMFactory ---")
            vision_llm = LLMFactory.create()
            vision_llm.load_model()
            print("--- Modelo listo para procesar ---")
        except Exception as e:
            print(f"Error cargando el modelo: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    try:
        # 2. Preparar la imagen para PIL (como pide moondream.py / qwen2vl.py)
        image_bytes = await image.read()
        pil_image = Image.open(io.BytesIO(image_bytes))
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        # 3. Prompt único: Extraer + Analizar
        # Este prompt le pide a la IA que haga todo el trabajo de una vez
        user_prompt = f"""
        Analyze this smartwatch image for user {user_id}.
        1. Extract: Heart rate, SpO2 (Oxygen), and Steps.
        2. Provide a brief health risk analysis based on these metrics.
        
        Return the result strictly as a JSON object with this format:
        {{
          "heart_rate": 0,
          "oxygen": 0,
          "steps": 0,
          "analysis": "text here"
        }}
        """

        start_time = time.time()

        # 4. Ejecutar tu lógica local (moondream.py o qwen2vl.py)
        # La función process_image ya tiene el extractor de JSON {}
        extracted_data = vision_llm.process_image(
            image=pil_image,
            prompt=user_prompt
        )

        total_time_ms = int((time.time() - start_time) * 1000)

        # 5. Respuesta para el frontend
        # Enviamos 'extracted_data' que es lo que React suele esperar
        return {
            "success": True,
            "extracted_data": extracted_data,
            "inference_time_ms": total_time_ms
        }

    except Exception as e:
        print(f"Error en el procesamiento: {e}")
        return {
            "success": False,
            "error_message": str(e)
        }

@app.get("/")
async def root():
    return {"message": "Medistruct API is running on port 8001"}