#!/usr/bin/env python3
"""
Script to verify that models are correctly installed and can be loaded.
"""
import sys
from pathlib import Path
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.factory import LLMFactory
import time


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"{text}")
    print(f"{'='*60}\n")


def verify_ollama():
    """Verify Ollama installation and models."""
    print_header("Verifying Ollama Installation")

    try:
        import requests

        # Check if Ollama is running
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            print("✓ Ollama service is running")

            # List available models
            models = response.json().get("models", [])
            if models:
                print(f"\n✓ Found {len(models)} Ollama model(s):")
                for model in models:
                    name = model.get("name", "unknown")
                    size = model.get("size", 0) / (1024**3)  # Convert to GB
                    print(f"  - {name} ({size:.2f} GB)")
                return True, [m.get("name") for m in models]
            else:
                print("\n⚠ Ollama is running but no models are installed")
                print("  Install a model with: ollama pull phi4")
                return True, []

        except requests.exceptions.ConnectionError:
            print("✗ Ollama service is not running")
            print("  Start with: ollama serve")
            return False, []

    except ImportError:
        print("✗ requests library not installed")
        return False, []


def verify_huggingface_cache():
    """Check HuggingFace cache for downloaded models."""
    print_header("Verifying HuggingFace Cache")

    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"

    if not cache_dir.exists():
        print("✗ HuggingFace cache directory not found")
        print(f"  Expected at: {cache_dir}")
        return []

    print(f"✓ Cache directory exists: {cache_dir}")

    # Look for model directories
    model_dirs = [d for d in cache_dir.iterdir() if d.is_dir() and d.name.startswith("models--")]

    if model_dirs:
        print(f"\n✓ Found {len(model_dirs)} cached model(s):")
        models = []
        for model_dir in model_dirs:
            # Parse model name from directory
            name = model_dir.name.replace("models--", "").replace("--", "/")

            # Get size
            size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
            size_gb = size / (1024**3)

            print(f"  - {name} ({size_gb:.2f} GB)")
            models.append(name)
        return models
    else:
        print("\n⚠ No models found in cache")
        print("  Download a model with:")
        print("    uv run python scripts/download_huggingface_model.py --model phi4")
        return []


def test_model_loading(model_type, model_name=None):
    """Test loading a specific model."""
    print_header(f"Testing Model: {model_type}")

    try:
        print(f"Attempting to create model instance...")
        start_time = time.time()

        llm = LLMFactory.create_llm(
            model_type=model_type,
            model_name=model_name,
            device="cpu"
        )

        creation_time = time.time() - start_time
        print(f"✓ Model instance created ({creation_time:.2f}s)")

        print(f"\nAttempting to load model...")
        start_time = time.time()

        llm.load_model()

        load_time = time.time() - start_time
        print(f"✓ Model loaded successfully ({load_time:.2f}s)")

        # Try to unload
        if hasattr(llm, 'unload_model'):
            llm.unload_model()
            print(f"✓ Model unloaded")

        return True

    except Exception as e:
        print(f"✗ Error loading model: {str(e)}")
        return False


def main():
    print_header("Model Installation Verification")

    # Check environment variables
    model_type = os.getenv("LLM_MODEL_TYPE", "not set")
    model_name = os.getenv("LLM_MODEL_NAME", "not set")
    device = os.getenv("DEVICE", "cpu")

    print("Environment Configuration:")
    print(f"  LLM_MODEL_TYPE: {model_type}")
    print(f"  LLM_MODEL_NAME: {model_name}")
    print(f"  DEVICE: {device}")

    # Verify Ollama
    ollama_running, ollama_models = verify_ollama()

    # Verify HuggingFace cache
    hf_models = verify_huggingface_cache()

    # Summary
    print_header("Summary")

    total_models = len(ollama_models) + len(hf_models)

    if total_models == 0:
        print("⚠ No models installed!")
        print("\nTo install models, run:")
        print("  bash scripts/install_models.sh")
        print("\nOr install manually:")
        print("  Ollama: bash scripts/setup_ollama.sh")
        print("  HuggingFace: uv run python scripts/download_huggingface_model.py --model phi4")
    else:
        print(f"✓ Total models available: {total_models}")
        print(f"  - Ollama: {len(ollama_models)}")
        print(f"  - HuggingFace: {len(hf_models)}")

    # Test loading if models are available
    if model_type != "not set" and model_type != "phi4":
        print(f"\n{'='*60}")
        response = input(f"Would you like to test loading {model_type}? (y/N): ")
        if response.lower() == 'y':
            test_model_loading(model_type, model_name if model_name != "not set" else None)

    print_header("Verification Complete")

    # Exit code based on models available
    sys.exit(0 if total_models > 0 else 1)


if __name__ == "__main__":
    main()
