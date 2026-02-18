# main.py
from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
import httpx
import uuid
import os

from database import sensor_collection
from models import SensorRequest, SensorResponse

# Crear la app FastAPI
app = FastAPI(title="SmartWatch Sensor API")

# ✅ Agregar el middleware CORS justo después de crear la app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # puedes poner ["http://localhost:3000"] si quieres restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta para guardar imágenes temporalmente
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# URL del servicio externo (simulada)
EXTERNAL_SERVICE_URL = "https://api.externo.com/procesar_imagen"


@app.post("/procesar_sensor/", response_model=SensorResponse)
async def procesar_sensor(
    nombre: str = Form(...),
    id_usuario: str = Form(...),
    imagen: UploadFile = None
):
    # 1️⃣ Validar imagen
    if not imagen:
        raise HTTPException(status_code=400, detail="Debe enviar una imagen del sensor")

    # 2️⃣ Guardar temporalmente la imagen
    image_name = f"{uuid.uuid4()}_{imagen.filename}"
    image_path = os.path.join(UPLOAD_DIR, image_name)

    async with aiofiles.open(image_path, 'wb') as out_file:
        content = await imagen.read()
        await out_file.write(content)

    # 3️⃣ Simular análisis del sensor
    async with httpx.AsyncClient() as client:
        try:
            files = {'imagen': (imagen.filename, open(image_path, 'rb'), imagen.content_type)}
            response = await client.post(EXTERNAL_SERVICE_URL, files=files)
            resultado_sensor = response.json()
        except Exception:
            resultado_sensor = {"bpm": 72, "oxigeno": 98, "estado": "estable"}

    # 4️⃣ Guardar resultado en MongoDB
    registro = {
        "id_usuario": id_usuario,
        "nombre": nombre,
        "ruta_imagen": image_path,
        "resultado_sensor": resultado_sensor,
    }
    await sensor_collection.insert_one(registro)

    # 5️⃣ Responder al cliente
    return SensorResponse(
        id_usuario=id_usuario,
        nombre=nombre,
        resultado_sensor=resultado_sensor,
        estado="procesado correctamente"
    )


@app.get("/consultar_resultado/")
async def consultar_resultado(id_usuario: str):
    registro = await sensor_collection.find_one(
        {"id_usuario": id_usuario},
        sort=[("_id", -1)]
    )

    if not registro:
        raise HTTPException(status_code=404, detail="No se encontraron datos para este usuario")

    return JSONResponse(content={
        "id_usuario": registro["id_usuario"],
        "nombre": registro["nombre"],
        "resultado_sensor": registro["resultado_sensor"],
        "ruta_imagen": registro["ruta_imagen"]
    })
