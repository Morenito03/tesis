import time
import io
import os
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from datetime import datetime # Para la fecha del registro
from pymongo import MongoClient # Para conectar a tu DB

# Importación absoluta desde tu carpeta src
from src.llm.factory import LLMFactory

app = FastAPI(title="smartwatch Single-IA Service")

# --- CONEXIÓN A MONGO DB ---
# Se conecta a tu base de datos y a la colección que pediste
client = MongoClient("mongodb://localhost:27017/")
db = client.smartwatch_db
collection = db.Embarazadas 

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variable global para mantener el modelo en RAM
vision_llm = None

@app.post("/process") 
async def process_image_all_in_one(
    image: UploadFile = File(...),
    nombre: str = Form(...),    # Nuevo: Recibimos el nombre
    telefono: str = Form(...),  # Nuevo: Recibimos el teléfono
    correo: str = Form(...),    # Nuevo: Recibimos el correo
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
        # 2. Preparar la imagen para PIL
        image_bytes = await image.read()
        pil_image = Image.open(io.BytesIO(image_bytes))
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        # 3. Prompt único: Extraer + Analizar
        user_prompt = """
Analiza esta imagen de un smartwatch. 
Extrae: 
- heart_rate (frecuencia cardiaca en BPM)
- oxygen (SpO2 en %)
- steps (pasos, si no hay pon 0)
- analysis (un breve comentario médico de 1 oración)

Devuelve SOLO un JSON con este formato:
{
  "heart_rate": 83,
  "oxygen": 98,
  "steps": 0,
  "analysis": "..."
}
"""

        start_time = time.time()

        # 4. Ejecutar la lógica local de la IA
        extracted_data = vision_llm.process_image(
            image=pil_image,
            prompt=user_prompt
        )

        total_time_ms = int((time.time() - start_time) * 1000)

        # --- 5. GUARDADO EN MONGODB (Lo que pediste) ---
        # Creamos el documento con la estructura para el Médico
        registro_paciente = {
            "nombre": nombre,
            "telefono": telefono,
            "correo": correo,
            "datos_salud": extracted_data, # Aquí va el JSON de la IA (BPM, Oxígeno, etc.)
            "fecha_analisis": datetime.now(),
            "i7_process_time": total_time_ms
        }
        
        # Insertamos en la colección 'Embarazadas'
        collection.insert_one(registro_paciente)
        print(f"✓ Registro de {nombre} guardado en smartwatch_db.")

        # 6. Respuesta para el frontend
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