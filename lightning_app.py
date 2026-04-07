"""Lightning.ai application configuration."""
import lightning as L
from lightning.app.components import ServeGradio
import uvicorn
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.api.fastapi_server import app


class FastAPIServer(L.LightningWork):
    """Lightning Work for FastAPI server."""

    def __init__(self, port: int = 8000, **kwargs):
        super().__init__(parallel=True, **kwargs)
        self.port = port

    def run(self):
        """Run the FastAPI server."""
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )


class GRPCServer(L.LightningWork):
    """Lightning Work for gRPC server."""

    def __init__(self, port: int = 50051, **kwargs):
        super().__init__(parallel=True, **kwargs)
        self.port = port

    def run(self):
        """Run the gRPC server."""
        from src.grpc_service.server import serve
        serve(port=self.port)


class SmartwatchLLMApp(L.LightningFlow):
    """Main Lightning application."""

    def __init__(self):
        super().__init__()
        # Create both servers
        self.fastapi_server = FastAPIServer()
        self.grpc_server = GRPCServer()

    def run(self):
        """Run both servers."""
        # Start FastAPI server
        self.fastapi_server.run()

        # Start gRPC server
        self.grpc_server.run()

    def configure_layout(self):
        """Configure the Lightning UI layout."""
        return [
            {
                "name": "FastAPI Service",
                "content": self.fastapi_server.url + "/docs"
            }
        ]


def create_app():
    """Create and return the Lightning app."""
    return L.LightningApp(SmartwatchLLMApp())


if __name__ == "__main__":
    app = create_app()
