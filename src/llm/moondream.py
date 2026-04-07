"""Moondream2 vision-language model implementation."""
import json
import os
import sys
from typing import Dict, Any
import importlib.util
from PIL import Image
import torch

from .base import BaseLLM


class MoondreamLLM(BaseLLM):
    """Moondream2 lightweight vision-language model (~1.8B params, ~4GB RAM).

    This implementation loads the model manually using a 'virtual package'
    strategy. This avoids both:
    1. 'attempted relative import' errors (by registering the snapshot
       as a proper Python package in sys.modules).
    2. 'all_tied_weights_keys' errors in newer transformers (by bypassing
       AutoModelForCausalLM entirely).
    """

    DEFAULT_REVISION = "2025-01-09"

    def __init__(
        self,
        model_name: str = "vikhyatk/moondream2",
        device: str = "cpu",
        revision: str = None
    ):
        """
        Initialize Moondream2 model.

        Args:
            model_name: HuggingFace model identifier
            device: Device to run on ('cpu', 'cuda', 'mps')
            revision: Model revision to use (pinned for stability)
        """
        super().__init__(model_name, device)
        self.revision = revision or self.DEFAULT_REVISION
        self.tokenizer = None

    def load_model(self) -> None:
        """Load Moondream2 using a robust virtual package strategy with native imports.
        
        This establishes 'moondream_repo' as a virtual package and uses
        importlib.import_module to load the core components. This allows
        Python's native import machinery to handle sub-dependencies correctly.
        """
        try:
            from huggingface_hub import snapshot_download
            from safetensors.torch import load_file as load_safetensors
            import importlib
            import types

            dtype = torch.float16 if "cuda" in self.device else torch.float32

            # Step 1: Download the model snapshot
            print(f"Loading Moondream2 (revision: {self.revision})...")
            model_path = snapshot_download(
                self.model_name,
                revision=self.revision,
            )
            print(f"Model files cached at: {model_path}")

            # Step 2: Establish the Virtual Package
            package_name = "moondream_repo"
            
            # Create the package module if it doesn't exist
            if package_name not in sys.modules:
                pkg_mod = types.ModuleType(package_name)
                pkg_mod.__path__ = [model_path]
                pkg_mod.__file__ = os.path.join(model_path, "__init__.py")
                pkg_mod.__package__ = package_name
                sys.modules[package_name] = pkg_mod
            
            # Add to sys.path to ensure absolute sub-imports work
            if model_path not in sys.path:
                sys.path.insert(0, model_path)

            # Step 3: Use native import machinery to load the model
            # This handles dependencies like image_crops, weights, etc. automatically
            try:
                # We import through the virtual package name
                config_mod = importlib.import_module(f"{package_name}.config")
                model_mod = importlib.import_module(f"{package_name}.moondream")
                
                # Step 4: Instantiate and load weights
                config = config_mod.MoondreamConfig()
                self.model = model_mod.MoondreamModel(config, dtype=dtype)
            except (ImportError, AttributeError) as e:
                print(f"  Note: Native package import failed ({e}), falling back to direct import...")
                # Fallback to direct import if virtual package namespacing fails
                import config as config_direct
                import moondream as model_direct
                config = config_direct.MoondreamConfig()
                self.model = model_direct.MoondreamModel(config, dtype=dtype)

            weights_file = os.path.join(model_path, "model.safetensors")
            if os.path.exists(weights_file):
                state_dict = load_safetensors(weights_file)
                self.model.load_state_dict(state_dict, strict=False)
            else:
                raise FileNotFoundError(f"model.safetensors not found in {model_path}")

            self.model = self.model.to(self.device).eval()
            self.tokenizer = self.model.tokenizer
            self.processor = self.tokenizer

            print(f"Moondream2 model loaded successfully on {self.device}")

        except Exception as e:
            print(f"Error loading Moondream2 model: {e}")
            raise

    def process_image(
        self,
        image: Image.Image,
        prompt: str,
        system_prompt: str = ""
    ) -> Dict[str, Any]:
        """
        Process image with Moondream2 model.

        Args:
            image: PIL Image object
            prompt: User prompt for the model
            system_prompt: System prompt with instructions

        Returns:
            Dictionary with extracted data from the image
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            # Construct full prompt
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

            # Use moondream's native query API
            result = self.model.query(image, full_prompt)
            answer = result.get("answer", "").strip()

            # Try to extract JSON from the answer
            try:
                start_idx = answer.find('{')
                end_idx = answer.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = answer[start_idx:end_idx]
                    extracted_data = json.loads(json_str)
                else:
                    extracted_data = {"raw_response": answer}
            except json.JSONDecodeError:
                extracted_data = {"raw_response": answer}

            return extracted_data

        except Exception as e:
            print(f"Error processing image with Moondream2: {e}")
            return {"error": str(e)}

    def unload_model(self) -> None:
        """Unload model from memory."""
        if self.model is not None:
            del self.model
            self.model = None
            self.processor = None
            self.tokenizer = None

            if self.device.startswith("cuda"):
                torch.cuda.empty_cache()
            print("Moondream2 model unloaded")
