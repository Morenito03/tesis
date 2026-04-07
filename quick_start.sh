#!/bin/bash
# Quick start script for Smartwatch LLM Service

echo "=============================================="
echo "Smartwatch LLM Service - Quick Start"
echo "=============================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo ""
echo "1. Installing system dependencies (libvips, etc.)..."
if [ -f scripts/install_system_deps.sh ]; then
    chmod +x scripts/install_system_deps.sh
    bash scripts/install_system_deps.sh
    if [ $? -ne 0 ]; then
        echo "Warning: System dependencies installation had issues."
        echo "The service may still work for some models (e.g., ollama)."
    fi
else
    echo "Warning: scripts/install_system_deps.sh not found, skipping system deps."
fi

echo ""
echo "2. Installing Python dependencies..."
uv sync

if [ $? -ne 0 ]; then
    echo "Error: Failed to install Python dependencies"
    exit 1
fi

echo ""
echo "3. Generating gRPC protobuf files..."
uv run python main.py generate-protos

if [ $? -ne 0 ]; then
    echo "Error: Failed to generate protobuf files"
    exit 1
fi

echo ""
echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo "  Run FastAPI server:"
echo "    uv run python main.py fastapi"
echo ""
echo "  Run gRPC server:"
echo "    uv run python main.py grpc"
echo ""
echo "  Test FastAPI:"
echo "    uv run python client/test_fastapi_client.py"
echo ""
echo "  Test gRPC:"
echo "    uv run python client/test_grpc_client.py <image_path>"
echo ""
echo "  View API docs:"
echo "    http://localhost:8001/docs  (or your FASTAPI_PORT)"
echo ""
echo "=============================================="
