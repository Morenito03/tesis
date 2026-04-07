"""Phi-4 multimodal model implementation."""
import json
from typing import Dict, Any
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForCausalLM

from .base import BaseLLM


class Phi4LLM(BaseLLM):
    """Phi-4 multimodal model implementation."""

    def __init__(self, model_name: str = "microsoft/phi-4", device: str = "cpu"):
        super().__init__(model_name, device)

    def load_model(self) -> None:
        """Load Phi-4 model and processor."""
        try:
            self.processor = AutoProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                dtype=torch.float16 if "cuda" in self.device else torch.float32,
                device_map=self.device,
                trust_remote_code=True
            )
            print(f"Phi-4 model loaded successfully on {self.device}")
        except Exception as e:
            print(f"Error loading Phi-4 model: {e}")
            raise

    def process_image(
        self,
        image: Image.Image,
        prompt: str,
        system_prompt: str = ""
    ) -> Dict[str, Any]:
        """Process image with Phi-4 model."""
        if self.model is None or self.processor is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            # Construct the full prompt
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

            # Prepare inputs
            inputs = self.processor(
                text=full_prompt,
                images=image,
                return_tensors="pt"
            ).to(self.device)

            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    do_sample=False,
                    temperature=0.0
                )

            # Decode response
            response = self.processor.decode(outputs[0], skip_special_tokens=True)

            # Extract JSON from response
            try:
                # Try to parse JSON from the response
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response[start_idx:end_idx]
                    extracted_data = json.loads(json_str)
                else:
                    extracted_data = {"raw_response": response}
            except json.JSONDecodeError:
                extracted_data = {"raw_response": response}

            return extracted_data

        except Exception as e:
            print(f"Error processing image: {e}")
            return {"error": str(e)}
