"""Main entry point for the smartwatch LLM service."""
import sys
import argparse
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required, use system env vars


def run_fastapi():
    """Run FastAPI server."""
    import uvicorn
    from src.api.fastapi_server import app

    port = int(os.getenv("FASTAPI_PORT", "8001"))
    print(f"FastAPI starting on port {port}")
    print(f"  → If on Lightning.ai, make sure port {port} is NOT 8000 (reserved by platform)")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


def run_grpc():
    """Run gRPC server."""
    from src.grpc_service.server import serve

    port = int(os.getenv("GRPC_PORT", "50051"))
    print(f"gRPC starting on port {port}")
    serve(port=port)


def generate_protos():
    """Generate protobuf files."""
    from src.grpc_service.generate_protos import generate_grpc_code
    success = generate_grpc_code()
    sys.exit(0 if success else 1)


def run_gradio():
    """Run Gradio interface with FastAPI server in background."""
    import threading
    import time
    import uvicorn
    import requests
    from src.api.fastapi_server import app as fastapi_app
    from src.ui.gradio_interface import launch

    fastapi_port = int(os.getenv("FASTAPI_PORT", "8001"))

    # Start FastAPI in a background daemon thread
    config = uvicorn.Config(
        fastapi_app,
        host="0.0.0.0",
        port=fastapi_port,
        log_level="warning"  # less verbose to keep Gradio logs clean
    )
    server = uvicorn.Server(config)
    fastapi_thread = threading.Thread(target=server.run, daemon=True)
    fastapi_thread.start()

    # Wait for FastAPI to be ready (up to 30 seconds)
    fastapi_url = f"http://localhost:{fastapi_port}"
    print(f"Waiting for FastAPI server to start on port {fastapi_port}...")
    for i in range(30):
        try:
            resp = requests.get(f"{fastapi_url}/", timeout=2)
            if resp.status_code == 200:
                print(f"✓ FastAPI server is ready at {fastapi_url}")
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    else:
        print(f"⚠ FastAPI server did not respond after 30s, starting Gradio anyway.")
        print(f"  The model may still be loading. FastAPI will be available once it finishes.")

    print(f"  → Use {fastapi_url} in Gradio (NOT the Lightning.ai public URL)")

    gradio_port = int(os.getenv("GRADIO_PORT", "7860"))
    launch(server_name="0.0.0.0", server_port=gradio_port, share=True)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Smartwatch LLM Service",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # FastAPI command
    subparsers.add_parser("fastapi", help="Run FastAPI server")

    # gRPC command
    subparsers.add_parser("grpc", help="Run gRPC server")

    # Generate protos command
    subparsers.add_parser("generate-protos", help="Generate protobuf files")

    # Gradio command
    subparsers.add_parser("gradio", help="Run Gradio UI interface")

    args = parser.parse_args()

    if args.command == "fastapi":
        print("Starting FastAPI server...")
        run_fastapi()
    elif args.command == "grpc":
        print("Starting gRPC server...")
        run_grpc()
    elif args.command == "generate-protos":
        print("Generating protobuf files...")
        generate_protos()
    elif args.command == "gradio":
        print("Starting Gradio interface...")
        run_gradio()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
