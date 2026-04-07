"""Pydantic models for FastAPI."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class SmartwatchRequest(BaseModel):
    """Request model for smartwatch image processing."""
    timestamp: str = Field(..., description="Hora de la petición")
    user_id: str = Field(..., description="Usuario que realiza la petición")
    command: str = Field(..., description="Orden o comando")
    description: str = Field(..., description="Texto de descripción")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-02-01T10:30:00",
                "user_id": "user123",
                "command": "extract_metrics",
                "description": "Extract health metrics from smartwatch screenshot"
            }
        }


class SmartwatchResponse(BaseModel):
    """Response model for smartwatch image processing."""
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    extracted_data: Dict[str, Any] = Field(..., description="Datos extraídos de la imagen")
    inference_time_ms: int = Field(..., description="Tiempo de inferencia en milisegundos")
    error_message: Optional[str] = Field(None, description="Mensaje de error si success=false")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "extracted_data": {
                    "heart_rate": "72 bpm",
                    "steps": "8543",
                    "calories": "450 kcal"
                },
                "inference_time_ms": 1250,
                "error_message": None
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    model_loading: bool = False
    model_name: str
