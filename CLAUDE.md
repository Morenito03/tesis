# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Smartwatch LLM Service** is a backend service for processing smartwatch screenshots using multimodal Large Language Models (LLMs). The service extracts health metrics and other data from images through three interfaces:
- **FastAPI** (REST API)
- **gRPC** (RPC protocol)
- **Gradio** (Web UI for testing both services)

The project is designed for deployment on **Lightning.ai** platform and uses **uv** as the package manager.

## Key Architecture Decisions

### 1. Flexible Model System
The LLM implementation uses a **Factory Pattern** (`src/llm/factory.py`) to allow easy switching between different multimodal models:
- Models can be changed via environment variables (`LLM_MODEL_TYPE`, `LLM_MODEL_NAME`)
- All models inherit from `BaseLLM` abstract class
- Predefined models: Phi-4, Gemma, Gemma 3n, LLaVA, Moondream, Qwen2-VL, Ollama
- Custom models can be loaded via HuggingFace identifiers or through Ollama

#### Available Predefined Models

| Model Type | HuggingFace ID | Description | Size |
|-----------|---------------|-------------|------|
| `phi4` | `microsoft/phi-4` | Microsoft Phi-4 multimodal model | ~7B |
| `gemma` | `google/gemma-3-2b-vision` | Google Gemma 3 2B vision model | ~2B |
| `gemma3n` | `google/gemma-3n-vision` | Google Gemma 3n vision model | Variable |
| `llava` | `llava-hf/llava-1.5-7b-hf` | LLaVA 1.5 model | ~7B |
| `moondream` | `vikhyatk/moondream2` | Moondream2 compact vision model | ~1.8B |
| `qwen2vl` | `Qwen/Qwen2-VL-2B-Instruct` | Qwen2 Vision Language 2B model | ~2B |
| `ollama` | Managed by Ollama | Phi-4 via Ollama (local deployment) | Variable |

To use a specific model:
```bash
# Via environment variable
export LLM_MODEL_TYPE=gemma3n
uv run python main.py fastapi

# Or in .env file
LLM_MODEL_TYPE=gemma3n
```

#### Using Ollama

The project supports using Phi-4 and other multimodal models through **Ollama**, which provides local model deployment with lower memory requirements and faster inference.

**Prerequisites:**
1. Install Ollama: https://ollama.ai
2. Pull a vision model:
   ```bash
   # Pull Phi-4 (recommended)
   ollama pull phi4

   # Or other vision models
   ollama pull llava
   ollama pull bakllava
   ```

**Configuration:**
```bash
# Set model type to ollama
export LLM_MODEL_TYPE=ollama

# Optional: Override Ollama host (defaults to http://localhost:11434)
export OLLAMA_HOST=http://localhost:11434

# Optional: Change the Ollama model (defaults to phi4)
export LLM_MODEL_NAME=llava

# Run the service
uv run python main.py fastapi
```

**Advantages of Ollama:**
- **Lower Memory Usage**: Models are optimized and quantized
- **Faster Inference**: Optimized runtime compared to vanilla Transformers
- **Easy Model Management**: Simple pull/push model operations
- **Multiple Model Support**: Switch between models without reloading
- **Local Deployment**: No external API calls required

**Ollama Model Names:**
When using `LLM_MODEL_TYPE=ollama`, you can specify different vision models via `LLM_MODEL_NAME`:
- `phi4` - Microsoft Phi-4 (default)
- `llava` - LLaVA 1.5
- `llava:13b` - LLaVA 1.5 13B
- `bakllava` - BakLLaVA (LLaVA with Mistral)

**Important Notes:**
- Ollama server must be running before starting the service
- The first request will verify the model is available and pull it if needed
- Models are managed by the Ollama daemon, not loaded into the Python process
- The `device` parameter is ignored when using Ollama (Ollama manages hardware acceleration)

### 2. Dual Interface Design
The service provides both FastAPI and gRPC interfaces that share the same underlying LLM processing:
- **FastAPI**: Located in `src/api/`, handles HTTP multipart form data
- **gRPC**: Located in `src/grpc_service/`, uses Protocol Buffers

Both services:
- Share the same system prompt for consistent behavior
- Track inference time
- Return JSON-formatted extracted data
- Handle errors gracefully

### 3. Protocol Buffers (gRPC)
- Definitions in `src/grpc_service/protos/smartwatch.proto`
- Generated Python code in `src/grpc_service/generated/`
- Must regenerate after `.proto` changes using `python main.py generate-protos`

## Common Development Commands

### Setup and Installation
```bash
# Install dependencies
uv sync

# Generate gRPC protobuf files (REQUIRED before running gRPC server)
uv run python main.py generate-protos
```

### Running Services
```bash
# Run FastAPI server (port 8000)
uv run python main.py fastapi

# Run gRPC server (port 50051)
uv run python main.py grpc

# Run Gradio UI interface (port 7860)
uv run python main.py gradio

# Alternative: Direct uvicorn
uv run uvicorn src.api.fastapi_server:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Option 1: Web UI (Gradio) - easiest way to test both services
uv run python main.py gradio
# Then open http://localhost:7860 in your browser

# Option 2: Command-line clients
# Test FastAPI service (health check + list models)
uv run python client/test_fastapi_client.py

# Test FastAPI with image
uv run python client/test_fastapi_client.py path/to/image.png

# Test gRPC service with image
uv run python client/test_grpc_client.py path/to/image.png
```

### Lightning.ai Deployment
```bash
# Deploy to Lightning.ai cloud
lightning run app lightning_app.py --cloud

# Run locally with Lightning
lightning run app lightning_app.py
```

## Project Structure

```
src/
├── api/                      # FastAPI REST interface
│   ├── fastapi_server.py     # Main FastAPI app with endpoints
│   └── models.py             # Pydantic models for request/response
├── grpc_service/             # gRPC interface
│   ├── server.py             # gRPC servicer implementation
│   ├── generate_protos.py    # Script to generate Python from .proto
│   ├── protos/               # Protocol Buffer definitions
│   │   └── smartwatch.proto
│   └── generated/            # Auto-generated gRPC code (gitignored)
├── llm/                      # LLM model implementations
│   ├── base.py               # Abstract base class (BaseLLM)
│   ├── phi4.py               # Phi-4 specific implementation
│   ├── ollama.py             # Ollama implementation for local deployment
│   ├── generic_multimodal.py # Generic implementation for other models
│   └── factory.py            # Factory pattern for model creation
├── ui/                       # User interface
│   └── gradio_interface.py   # Gradio web UI for testing services
└── utils/                    # Utility functions
client/
├── test_fastapi_client.py    # FastAPI test client
└── test_grpc_client.py       # gRPC test client
```

## Important Implementation Details

### System Prompt
Both services use the same system prompt (defined in their respective server files) that instructs the LLM to:
- Extract smartwatch metrics (heart rate, steps, calories, etc.)
- Return data in JSON format
- Handle various types of smartwatch screenshots

### Request Flow
1. Client sends image + metadata (timestamp, user_id, command, description)
2. Service loads LLM model (lazy loading on first request)
3. Image converted to PIL Image (RGB)
4. Prompt constructed from system prompt + user metadata
5. LLM processes image with prompt
6. Response extracted and parsed as JSON
7. Inference time tracked and returned

### Model Loading Strategy
- Models are loaded lazily on first request (not at startup)
- This prevents startup delays and memory usage when model isn't needed
- Models can be unloaded to free memory via `unload_model()`

### Error Handling
- Both services return structured error responses with `success: false`
- Inference errors are caught and returned in `error_message` field
- Invalid images and file errors handled gracefully

## Adding New Models

To add a new multimodal model:

1. **Option A: Use GenericMultimodalLLM**
   ```python
   # In src/llm/factory.py, add to MODEL_CONFIGS:
   "newmodel": {
       "class": GenericMultimodalLLM,
       "model_name": "org/model-name",
       "use_vision2seq": False  # or True depending on model
   }
   ```

2. **Option B: Create Custom Implementation**
   - Create new file in `src/llm/` extending `BaseLLM`
   - Implement `load_model()` and `process_image()` methods
   - Add to `MODEL_CONFIGS` in factory.py

3. **Test the new model**
   ```bash
   export LLM_MODEL_TYPE=newmodel
   uv run python client/test_fastapi_client.py test_image.png
   ```

## Modifying Protocol Buffers

When changing `smartwatch.proto`:

1. Edit `src/grpc_service/protos/smartwatch.proto`
2. Regenerate Python code: `uv run python main.py generate-protos`
3. Update `src/grpc_service/server.py` if service signature changed
4. Update `client/test_grpc_client.py` if request/response changed
5. Test with gRPC client

## Configuration via Environment Variables

Create a `.env` file (see `.env.example`):
```bash
LLM_MODEL_TYPE=phi4        # or gemma, gemma3n, llava, moondream, qwen2vl, ollama
LLM_MODEL_NAME=phi4        # When using ollama: phi4, llava, bakllava, etc.
DEVICE=cpu                 # or cuda for GPU (not used with ollama)
OLLAMA_HOST=http://localhost:11434  # Ollama server URL (only for ollama type)
FASTAPI_PORT=8000
GRPC_PORT=50051
```

The factory checks environment variables automatically and overrides defaults.

## Dependencies

Key dependencies managed in `pyproject.toml`:
- `fastapi` + `uvicorn`: REST API
- `grpcio` + `grpcio-tools`: gRPC support
- `torch` + `transformers`: LLM inference
- `ollama`: Ollama Python client for local model deployment
- `lightning`: Deployment platform
- `pydantic`: Data validation
- `pillow`: Image processing
- `gradio`: Web UI for testing
- `requests`: HTTP client for Gradio interface

## Common Issues and Solutions

### gRPC Import Errors
- **Problem**: `ImportError: cannot import name 'smartwatch_pb2'`
- **Solution**: Run `uv run python main.py generate-protos`

### Model Loading Failures
- **Problem**: Model fails to load or CUDA out of memory
- **Solution**:
  - Use `DEVICE=cpu` for CPU inference
  - Try smaller models (phi4, moondream)
  - Reduce batch size in model generation

### Port Already in Use
- **Problem**: `OSError: [Errno 48] Address already in use`
- **Solution**: Kill existing process or change port in `.env`

### Ollama Connection Issues
- **Problem**: `Error initializing Ollama client: connection refused`
- **Solution**:
  - Ensure Ollama is installed and running: `ollama serve`
  - Check Ollama is listening on the correct port: `curl http://localhost:11434/api/tags`
  - Update `OLLAMA_HOST` in `.env` if using a custom URL

### Ollama Model Not Found
- **Problem**: `Model 'phi4' not found in Ollama`
- **Solution**: Pull the model first: `ollama pull phi4`
- The service will attempt to auto-pull the model, but manual pulling is faster

### Qwen2-VL Configuration Issues
- **Problem**: `Unrecognized configuration class Qwen2VLConfig for AutoModelForCausalLM`
- **Solution**: Ensure transformers version is recent (>=4.40+) with `trust_remote_code=True` support
  - Qwen2-VL has a dedicated implementation in `src/llm/qwen2vl.py`
  - It automatically selects the correct model class based on available transformers features
  - Model will load with `Qwen2VLForConditionalGeneration` if available, otherwise falls back to `AutoModel`

## Performance Considerations

- **Inference Time**: Varies by model (1-5 seconds on CPU, faster on GPU)
- **Memory Usage**: ~4-8GB RAM depending on model size
- **Concurrent Requests**: Use `max_workers` in gRPC or `workers` in uvicorn
- **Model Caching**: HuggingFace models cached in `~/.cache/huggingface/`

## Testing Strategy

1. **Unit Tests**: Place in `tests/` directory (pytest)
2. **Integration Tests**: Use provided client scripts
3. **Manual Testing**:
   - **Gradio UI**: `uv run python main.py gradio` then open `http://localhost:7860`
   - **FastAPI docs**: `http://localhost:8000/docs`
4. **Load Testing**: Consider using tools like `locust` or `hey`

## Gradio UI Interface

The Gradio interface (`src/ui/gradio_interface.py`) provides a user-friendly web UI for testing both FastAPI and gRPC services.

### Features
- **Image Upload**: Drag and drop or click to upload smartwatch screenshots
- **Service Selection**: Toggle between FastAPI and gRPC testing
- **Metadata Input**: Configure timestamp, user_id, command, and description
- **Real-time Results**: View extracted data and inference time
- **Error Handling**: Clear error messages for connection and processing issues

### Usage
```bash
# Start the Gradio interface
uv run python main.py gradio

# Access the interface at http://localhost:7860
```

### Configuration
- **FastAPI**: Defaults to `http://localhost:8000`
- **gRPC**: Defaults to `localhost:50051`
- Both can be configured in the UI

### Important Notes
- The respective service (FastAPI or gRPC) must be running before testing
- For gRPC testing, ensure protobuf files are generated: `uv run python main.py generate-protos`
- The interface makes HTTP requests to FastAPI and gRPC calls to the gRPC service
- Results are formatted with JSON pretty-printing for readability
