#!/usr/bin/env python3
"""
Script to pre-download HuggingFace models and their weights.
This downloads the model weights to cache (~/.cache/huggingface/) to avoid
downloading during runtime.
"""
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from transformers import AutoTokenizer, AutoProcessor, AutoModelForCausalLM
from PIL import Image
import torch
import os


# Model configurations matching factory.py
MODEL_CONFIGS = {
    "phi4": {
        "model_name": "microsoft/phi-4",
        "use_vision2seq": False
    },
    "gemma": {
        "model_name": "google/gemma-3-2b-vision",
        "use_vision2seq": False
    },
    "gemma3n": {
        "model_name": "google/gemma-3n-vision",
        "use_vision2seq": False
    },
    "llava": {
        "model_name": "llava-hf/llava-1.5-7b-hf",
        "use_vision2seq": True
    },
    "moondream": {
        "model_name": "vikhyatk/moondream2",
        "use_vision2seq": False
    },
    "qwen2vl": {
        "model_name": "Qwen/Qwen2-VL-2B-Instruct",
        "use_vision2seq": False
    }
}


def download_model(model_type: str, device: str = "cpu"):
    """
    Download a specific model and its weights.

    Args:
        model_type: One of phi4, gemma, gemma3n, llava, moondream
        device: Device to use (cpu or cuda)
    """
    if model_type not in MODEL_CONFIGS:
        print(f"Error: Unknown model type '{model_type}'")
        print(f"Available models: {', '.join(MODEL_CONFIGS.keys())}")
        return False

    config = MODEL_CONFIGS[model_type]
    model_name = config["model_name"]
    use_vision2seq = config["use_vision2seq"]

    print(f"\n{'='*60}")
    print(f"Downloading model: {model_type}")
    print(f"HuggingFace ID: {model_name}")
    print(f"Device: {device}")
    print(f"{'='*60}\n")

    try:
        # Download tokenizer/processor
        print(f"[1/3] Downloading tokenizer/processor...")
        try:
            processor = AutoProcessor.from_pretrained(
                model_name,
                trust_remote_code=True
            )
            print("  ✓ Processor downloaded")
        except Exception as e:
            print(f"  ⚠ Processor not available, trying tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True
            )
            print("  ✓ Tokenizer downloaded")

        # Download model
        print(f"\n[2/3] Downloading model weights...")
        print(f"  This may take several minutes depending on model size...")

        if use_vision2seq:
            try:
                from transformers import AutoModelForVision2Seq
            except ImportError:
                from transformers import AutoModelForCausalLM as AutoModelForVision2Seq
            model = AutoModelForVision2Seq.from_pretrained(
                model_name,
                trust_remote_code=True,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                trust_remote_code=True,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32
            )

        print("  ✓ Model weights downloaded")

        # Test model loading
        print(f"\n[3/3] Verifying model can load...")
        model = model.to(device)
        print(f"  ✓ Model successfully loaded to {device}")

        # Get model size
        param_count = sum(p.numel() for p in model.parameters())
        print(f"\n  Model parameters: {param_count:,} ({param_count/1e9:.2f}B)")

        # Get cache location
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        print(f"  Cache location: {cache_dir}")

        print(f"\n{'='*60}")
        print(f"✓ Model '{model_type}' successfully downloaded and verified!")
        print(f"{'='*60}\n")

        return True

    except Exception as e:
        print(f"\n✗ Error downloading model: {str(e)}")
        print(f"{'='*60}\n")
        return False


def download_all_models(device: str = "cpu"):
    """Download all available models."""
    print(f"\n{'='*60}")
    print("Downloading ALL models")
    print(f"{'='*60}")
    print(f"\nThis will download {len(MODEL_CONFIGS)} models:")
    for model_type, config in MODEL_CONFIGS.items():
        print(f"  - {model_type}: {config['model_name']}")

    print(f"\n⚠ WARNING: This will download several GB of data!")
    response = input("\nContinue? (y/N): ")

    if response.lower() != 'y':
        print("Cancelled.")
        return

    results = {}
    for model_type in MODEL_CONFIGS.keys():
        success = download_model(model_type, device)
        results[model_type] = success

    # Summary
    print(f"\n{'='*60}")
    print("Download Summary")
    print(f"{'='*60}")
    for model_type, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {model_type}")
    print(f"{'='*60}\n")


def list_models():
    """List all available models."""
    print(f"\n{'='*60}")
    print("Available HuggingFace Models")
    print(f"{'='*60}\n")

    for model_type, config in MODEL_CONFIGS.items():
        print(f"  {model_type}")
        print(f"    HuggingFace ID: {config['model_name']}")
        print(f"    Vision2Seq: {config['use_vision2seq']}")
        print()

    print(f"Usage:")
    print(f"  python scripts/download_huggingface_model.py --model phi4")
    print(f"  python scripts/download_huggingface_model.py --all")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Download HuggingFace models for Smartwatch LLM Service"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Model type to download (phi4, gemma, gemma3n, llava, moondream, qwen2vl)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all available models"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available models"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device to use for verification (default: cpu)"
    )

    args = parser.parse_args()

    if args.list:
        list_models()
    elif args.all:
        download_all_models(args.device)
    elif args.model:
        download_model(args.model, args.device)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
