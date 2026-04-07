# Smartwatch LLM Service

Backend service for processing smartwatch screenshots using multimodal LLMs. The service provides **FastAPI** (REST), **gRPC**, and **Gradio** (Web UI) interfaces for extracting data from smartwatch images.

## Features

- 🚀 **Triple Interface**: FastAPI (REST), gRPC, and Gradio (Web UI) support
- 🎨 **User-Friendly UI**: Gradio web interface for easy testing of both services
- 🧠 **Flexible LLM Backend**: Support for multiple multimodal models (Phi-4, Gemma, Gemma 3n, LLaVA, Moondream, Ollama)
- 🔄 **Easy Model Switching**: Change models via environment variables without code changes
- ⚡ **Lightning.ai Ready**: Configured for deployment on Lightning.ai platform
- 📊 **Model Status Indicator**: Real-time model loading status in the Gradio UI
- 🧪 **Test Clients**: Comprehensive test clients for both FastAPI and gRPC
- � **Inference Tracking**: Built-in timing for LLM inference

## Supported Models

| Model | Type | Params | RAM Required | Best For |
|-------|------|--------|-------------|----------|
| **Moondream** (vikhyatk/moondream2) | HuggingFace | ~1.8B | ~4 GB | ⭐ Lightweight / Cloud |
| **Gemma** (google/gemma-3-2b-vision) | HuggingFace | ~2B | ~6 GB | Balanced |
| **Gemma 3n** (google/gemma-3n-vision) | HuggingFace | — | ~8 GB | Newer architecture |
| **LLaVA** (llava-hf/llava-1.5-7b-hf) | HuggingFace | ~7B | ~14 GB | High accuracy |
| **Phi-4** (microsoft/phi-4) | HuggingFace | ~7B | ~28 GB | Full featured |
| **Ollama** (any vision model) | Ollama | — | Varies | ⭐ Production |

> **💡 Recommendation:** Use **Moondream** for development/cloud (low memory), **Ollama** for production (optimized inference).

## Quick Start

### 1. Install System Dependencies

The project requires some system-level libraries (e.g., `libvips` for image processing).

**On Lightning.ai / Ubuntu / Debian:**
```bash
# Run the automated script
bash scripts/install_system_deps.sh

# Or install manually
apt-get update && apt-get install -y libvips42 libvips-dev
```

**On Fedora / RHEL:**
```bash
sudo dnf install -y vips vips-devel
```

**On macOS:**
```bash
brew install vips
```

**On Windows:**
> `libvips` is not required on Windows — `pyvips` includes pre-built binaries.

### 2. Install Python Dependencies

```bash
# Quick setup (installs system deps + Python deps + generates protos)
bash quick_start.sh

# Or manually with uv
uv sync
uv run python main.py generate-protos
```

### 3. Configure Environment

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Default `.env` settings (recommended for Lightning.ai):
```bash
LLM_MODEL_TYPE=moondream     # Lightweight model (~4 GB RAM)
FASTAPI_PORT=8001            # Port 8000 is reserved on Lightning.ai
DEVICE=cpu                   # Use 'cuda' for GPU
```

### 4. Install Models

**Option A: Automated Installation (Recommended)**

Linux/macOS:
```bash
bash scripts/install_models.sh
```

Windows (PowerShell):
```powershell
.\scripts\install_models.ps1
```

**Option B: Manual Installation**

For Ollama (recommended for faster inference):
```bash
# Install Ollama: https://ollama.ai/download
bash scripts/setup_ollama.sh

# Configure
echo "LLM_MODEL_TYPE=ollama" >> .env
echo "LLM_MODEL_NAME=phi4" >> .env
```

For HuggingFace models:
```bash
# Download specific model
uv run python scripts/download_huggingface_model.py --model phi4

# Configure
echo "LLM_MODEL_TYPE=phi4" >> .env
echo "DEVICE=cpu" >> .env  # or cuda
```

See [scripts/README.md](scripts/README.md) for detailed model installation guide.

### 5. Run the Service

```bash
# Start Gradio UI (launches FastAPI internally + web interface)
uv run python main.py gradio

# Or start FastAPI server standalone
uv run python main.py fastapi
```

> **📍 Note:** On Lightning.ai, the Gradio UI will be available through the public URL on port 8080. FastAPI runs internally on port 8001 (configurable via `FASTAPI_PORT`).

## Installation

### Prerequisites

- **Python >= 3.11**
- **uv** (recommended) or pip
- **System libraries**: `libvips` (see [System Dependencies](#1-install-system-dependencies) above)

### Using uv (Recommended)

```bash
# Install dependencies
uv sync

# Generate gRPC protobuf files
uv run python main.py generate-protos
```

### Using pip

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Generate gRPC protobuf files
python main.py generate-protos
```

## Usage

### Running FastAPI Server

```bash
# Using uv (default port: 8001)
uv run python main.py fastapi

# Or directly with uvicorn
uv run uvicorn src.api.fastapi_server:app --host 0.0.0.0 --port 8001

# Access interactive docs at: http://localhost:8001/docs
```

> **⚠️ Lightning.ai:** Port 8000 is reserved by the platform. Always use port 8001+ (set `FASTAPI_PORT=8001` in `.env`).

### Running gRPC Server

```bash
# Using uv
uv run python main.py grpc

# Server will start on port 50051
```

### Running Gradio UI

```bash
# Using uv
uv run python main.py gradio

# Access the web interface at: http://localhost:7860
```

The Gradio interface provides an easy-to-use web UI for testing both FastAPI and gRPC services. Simply upload a smartwatch screenshot and choose which service to test.

### Running on Lightning.ai

```bash
# Option 1: Deploy via Lightning CLI
lightning run app lightning_app.py --cloud

# Option 2: Run directly in a Lightning.ai Cloudspace terminal
bash scripts/install_system_deps.sh   # Install libvips (once)
uv sync                                # Install Python deps
uv run python main.py gradio           # Start Gradio + FastAPI
```

**Lightning.ai important notes:**
- Port **8000** is **reserved** by the platform — use `FASTAPI_PORT=8001`
- The Gradio UI auto-starts FastAPI in a background thread
- Model loading is non-blocking; the status indicator shows loading progress
- Use **moondream** (default) to avoid OOM — it only needs ~4 GB RAM

## Configuration

Create a `.env` file (see `.env.example` for template):

### Environment Variables

```bash
# Model configuration
LLM_MODEL_TYPE=moondream     # moondream, ollama, phi4, gemma, gemma3n, llava
LLM_MODEL_NAME=phi4          # Model name (for ollama: phi4, llava, bakllava, etc.)

# Ollama configuration (only for LLM_MODEL_TYPE=ollama)
OLLAMA_HOST=http://localhost:11434

# Device configuration (not used for ollama)
DEVICE=cpu                   # Use 'cuda' for GPU

# Service ports
FASTAPI_PORT=8001            # ⚠️ Use 8001+ on Lightning.ai (8000 is reserved)
GRPC_PORT=50051
```

### Changing Models

You can change models in three ways:

1. **Environment Variables** (Recommended)
```bash
# For Ollama
export LLM_MODEL_TYPE=ollama
export LLM_MODEL_NAME=phi4

# For HuggingFace models
export LLM_MODEL_TYPE=gemma3n
export DEVICE=cpu
```

2. **Code Configuration**
```python
from src.llm.factory import LLMFactory
llm = LLMFactory.create_llm(model_type="phi4", device="cpu")
```

3. **Custom Model**
```bash
export LLM_MODEL_NAME="custom/model-identifier"
```

### Ollama vs HuggingFace

| Feature | Ollama | HuggingFace |
|---------|--------|-------------|
| Speed | ⚡ Faster (optimized) | Slower |
| Memory | 💾 Lower (quantized) | Higher |
| Setup | ✅ Simple | Auto-download |
| Models | Limited to Ollama catalog | Full HuggingFace access |

**Recommendation**: Use Ollama for production, HuggingFace for experimentation.

## Testing

### Option 1: Gradio Web UI (Easiest)

```bash
# Start the Gradio interface
uv run python main.py gradio

# Open http://localhost:7860 in your browser
# Upload an image and test both FastAPI and gRPC services
```

### Option 2: Command-Line Clients

#### Test FastAPI Service

```bash
# Health check and model info
uv run python client/test_fastapi_client.py

# Test with image
uv run python client/test_fastapi_client.py path/to/smartwatch_image.png
```

#### Test gRPC Service

```bash
# Test with image
uv run python client/test_grpc_client.py path/to/smartwatch_image.png
```

## API Examples

### FastAPI (REST)

```bash
curl -X POST "http://localhost:8001/process" \
  -F "image=@smartwatch.png" \
  -F "timestamp=2026-02-01T10:30:00" \
  -F "user_id=user123" \
  -F "command=extract_metrics" \
  -F "description=Extract health metrics"
```

### gRPC

See `client/test_grpc_client.py` for example implementation.

## Project Structure

```
curso_platzy/
├── src/
│   ├── api/                 # FastAPI implementation
│   │   ├── fastapi_server.py
│   │   └── models.py
│   ├── grpc_service/        # gRPC implementation
│   │   ├── server.py
│   │   ├── protos/          # Protocol buffer definitions
│   │   └── generated/       # Generated gRPC code
│   ├── llm/                 # LLM implementations
│   │   ├── base.py          # Abstract base class
│   │   ├── phi4.py          # Phi-4 implementation
│   │   ├── moondream.py     # Moondream2 implementation
│   │   ├── generic_multimodal.py  # Gemma, LLaVA, etc.
│   │   ├── ollama.py        # Ollama backend
│   │   └── factory.py       # Model factory
│   ├── ui/                  # User interface
│   │   └── gradio_interface.py  # Gradio web UI
│   └── utils/               # Utility functions
├── scripts/                 # Setup & utility scripts
│   ├── install_system_deps.sh   # System dependencies (libvips, etc.)
│   ├── install_models.sh        # Model installation
│   ├── install_models.ps1       # Model installation (Windows)
│   ├── setup_ollama.sh          # Ollama setup
│   ├── download_huggingface_model.py
│   └── verify_models.py
├── client/                  # Test clients
│   ├── test_fastapi_client.py
│   └── test_grpc_client.py
├── tests/                   # Unit tests
├── .env.example             # Environment template
├── lightning_app.py         # Lightning.ai configuration
├── main.py                  # Main entry point
├── quick_start.sh           # Full setup script
└── pyproject.toml           # Dependencies
```

## Development

### Generate Protobuf Files

After modifying `.proto` files:

```bash
uv run python main.py generate-protos
```

### Adding New Models

1. Create a new class in `src/llm/` that extends `BaseLLM`
2. Add configuration to `LLMFactory.MODEL_CONFIGS`
3. Test with both FastAPI and gRPC clients

## Response Format

Both services return JSON with the following structure:

```json
{
  "success": true,
  "extracted_data": {
    "heart_rate": "72 bpm",
    "steps": "8543",
    "calories": "450 kcal"
  },
  "inference_time_ms": 1250,
  "error_message": null
}
```

## Requirements

### System Dependencies
- **libvips** — Required by `pyvips` for image processing (Moondream model)
  - Ubuntu/Debian: `apt-get install libvips-dev`
  - Fedora/RHEL: `dnf install vips-devel`
  - macOS: `brew install vips`
  - Windows: Not needed (bundled with `pyvips`)

### Python Dependencies
- Python >= 3.11
- PyTorch (CPU or CUDA)
- FastAPI + Uvicorn
- gRPC + gRPC Tools
- Gradio >= 5.0 (Web UI)
- Transformers + einops + timm + pyvips
- Lightning (for deployment)
- Ollama (optional, for optimized inference)

## Model Installation Guide

For detailed information about installing and managing models, see the [Model Installation Guide](scripts/README.md).

### Quick Reference

**Install all tools and models:**
```bash
# Linux/macOS
bash scripts/install_models.sh

# Windows
.\scripts\install_models.ps1
```

**Download specific HuggingFace model:**
```bash
uv run python scripts/download_huggingface_model.py --model phi4
```

**Setup Ollama:**
```bash
bash scripts/setup_ollama.sh
```

**List available models:**
```bash
# HuggingFace
uv run python scripts/download_huggingface_model.py --list

# Ollama
ollama list
```

## Troubleshooting

### System Dependencies
- **`libvips.so.42: cannot open shared object file`**: Install libvips system library:
  ```bash
  # Lightning.ai / Ubuntu / Debian
  apt-get update && apt-get install -y libvips42 libvips-dev
  # Or use the script
  bash scripts/install_system_deps.sh
  ```
- **`No module named 'einops'`** / **`No module named 'timm'`**: Run `uv sync` to install all Python dependencies.

### Lightning.ai / Port Issues
- **Port 8000 not reachable**: Port 8000 is **reserved** by Lightning.ai. Set `FASTAPI_PORT=8001` in `.env`.
- **Gradio can't reach FastAPI**: In the Gradio UI, use `http://localhost:8001` (not the public Lightning URL).
- **Process killed (OOM)**: Use a smaller model. Set `LLM_MODEL_TYPE=moondream` in `.env` (~4 GB RAM).

### Model Download Issues
- **Slow downloads**: HuggingFace models are large (4-14 GB). Consider using Ollama for faster setup.
- **Out of memory**: Try smaller models (moondream ~4 GB, gemma ~6 GB) or use Ollama's quantized versions.
- **CUDA errors**: Set `DEVICE=cpu` in `.env` if GPU is unavailable.

### Ollama Issues
- **Connection refused**: Ensure Ollama is running with `ollama serve`
- **Model not found**: Pull the model first with `ollama pull phi4`

### gRPC Errors
- **Import errors**: Regenerate protobuf files with `uv run python main.py generate-protos`

## Performance Tips

1. **Use Ollama for production**: 2-3x faster inference with lower memory usage
2. **Choose appropriate model size**:
   - Cloud/Testing: **moondream** (~1.8B, ~4 GB RAM) ⭐
   - Balanced: gemma (~2B, ~6 GB RAM)
   - High accuracy: llava, phi4 (~7B, ~14-28 GB RAM)
3. **Use GPU when available**: Set `DEVICE=cuda` (HuggingFace only)
4. **Pre-download models**: Avoid delays on first request
5. **On Lightning.ai**: Moondream is the recommended default to avoid OOM kills


## Bibliografy

- [Deploy Phi3.5 Vision API with LitServe](https://lightning.ai/lightning-ai/environments/deploy-phi3-5-vision-api-with-litserve?view=public&section=featured&query=phi4)

- [Run Google Gemma 2B LLM on Cloud GPUs](https://lightning.ai/lightning-ai/environments/run-google-gemma-2b-llm-on-cloud-gpus?view=public&section=featured&query=gemma)

- [Deploy Gemma 3 Multimodal Multilingual model](https://lightning.ai/sitammeur/environments/deploy-gemma-3-multimodal-multilingual-model?view=public&section=featured&query=gemma)

- [Deploy PaliGemma 2 mix Vision-Language model](https://lightning.ai/sitammeur/environments/deploy-paligemma-2-mix-vision-language-model?view=public&section=featured&query=gemma)

## License

MIT
