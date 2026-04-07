"""FastAPI module for HTTP endpoints."""
from .fastapi_server import app
from .models import SmartwatchRequest, SmartwatchResponse, HealthCheckResponse

__all__ = [
    "app",
    "SmartwatchRequest",
    "SmartwatchResponse",
    "HealthCheckResponse"
]
