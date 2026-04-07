"""Generic multimodal model implementation for various small models."""
import json
from typing import Dict, Any
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForCausalLM

from .base import BaseLLM


class GenericMultimodalLLM(BaseLLM):
    """Generic implementation for multimodal models like Gemma, LLaVA, etc."""

    def __init__(
        self,
        model_name: str,
        device: str = "cpu",
        use_vision2seq: bool = False
    ):
        """
        Initialize generic multimodal model.

        Args:
            model_name: HuggingFace model identifier
            device: Device to run on
            use_vision2seq: Whether to use Vision2Seq architecture
        """
        super().__init__(model_name, device)
        self.use_vision2seq = use_vision2seq

    def load_model(self) -> None:
        """Load the model and processor."""
        try:
            self.processor = AutoProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )

            # Choose appropriate model class
            if self.use_vision2seq:
                try:
                    from transformers import AutoModelForVision2Seq
                except ImportError:
                    from transformers import AutoModelForCausalLM as AutoModelForVision2Seq
                model_class = AutoModelForVision2Seq
            else:
                model_class = AutoModelForCausalLM

            self.model = model_class.from_pretrained(
                self.model_name,
                dtype=torch.float16 if "cuda" in self.device else torch.float32,
                device_map=self.device,
                trust_remote_code=True
            )
            print(f"Model {self.model_name} loaded successfully on {self.device}")
        except Exception as e:
            print(f"Error loading model {self.model_name}: {e}")
            raise

    def process_image(
        self,
        image: Image.Image,
        prompt: str,
        system_prompt: str = ""
    ) -> Dict[str, Any]:
        """Process image with the loaded model."""
        if self.model is None or self.processor is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            # Construct full prompt
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
