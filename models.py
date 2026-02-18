# models.py
from pydantic import BaseModel
from typing import Optional

class SensorRequest(BaseModel):
    nombre: str
    id_usuario: str

class SensorResponse(BaseModel):
    id_usuario: str
    nombre: str
    resultado_sensor: dict
    estado: str
