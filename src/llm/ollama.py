"""Ollama multimodal model implementation."""
import json
import base64
from io import BytesIO
from typing import Dict, Any
from PIL import Image
import ollama

from .base import BaseLLM


class OllamaLLM(BaseLLM):
    """Ollama multimodal model implementation."""

    def __init__(
        self,
        model_name: str = "phi4",
        device: str = "cpu",
        host: str = "http://localhost:11434"
    ):
        """
        Initialize Ollama LLM.

        Args:
            model_name: Name of the Ollama model (e.g., 'phi4', 'llava', 'bakllava')
            device: Not used for Ollama (kept for compatibility with BaseLLM)
            host: Ollama server host URL
        """
        super().__init__(model_name, device)
        self.host = host
        self.client = None

    def load_model(self) -> None:
        """
        Initialize Ollama client connection.

        Note: Ollama models are managed by the Ollama daemon,
        so this method only verifies the connection and model availability.
        """
        try:
            # Initialize client with custom host if provided
            self.client = ollama.Client(host=self.host)

            # Verify model is available
            try:
                models = self.client.list()
                available_models = [m['name'] for m in models['models']]

                # Check if the exact model or a variant is available
                model_exists = any(
                    self.model_name in model_name
                    for model_name in available_models
                )

                if not model_exists:
                    print(f"Warning: Model '{self.model_name}' not found in Ollama.")
                    print(f"Available models: {', '.join(available_models)}")
                    print(f"Attempting to pull model '{self.model_name}'...")

                    # Try to pull the model
                    self.client.pull(self.model_name)
                    print(f"Model '{self.model_name}' pulled successfully.")
                else:
                    print(f"Ollama model '{self.model_name}' is available.")

            except Exception as e:
                print(f"Warning: Could not verify model availability: {e}")
                print(f"Will attempt to use model '{self.model_name}' anyway.")

            self.model = True  # Flag to indicate client is ready
            print(f"Ollama client initialized successfully (host: {self.host})")

        except Exception as e:
            print(f"Error initializing Ollama client: {e}")
            raise

    def _image_to_base64(self, image: Image.Image) -> str:
        """
        Convert PIL Image to base64 string.

        Args:
            image: PIL Image object

        Returns:
            Base64 encoded string of the image
        """
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        return base64.b64encode(img_bytes).decode('utf-8')

    def process_image(
        self,
        image: Image.Image,
        prompt: str,
        system_prompt: str = ""
    ) -> Dict[str, Any]:
        """
        Process image with Ollama model.

        Args:
            image: PIL Image object
            prompt: User prompt for the model
            system_prompt: System prompt with instructions

        Returns:
            Dictionary with extracted data from the image
        """
        if self.client is None or self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            # Convert image to base64
            image_b64 = self._image_to_base64(image)

            # Construct the full prompt
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

            # Prepare messages for chat API
            messages = [
                {
                    'role': 'user',
                    'content': full_prompt,
                    'images': [image_b64]
                }
            ]

            # Call Ollama API
            response = self.client.chat(
                model=self.model_name,
                messages=messages,
                options={
                    'temperature': 0.0,
                    'num_predict': 512,
                }
            )

            # Extract response text
            response_text = response['message']['content']

            # Extract JSON from response
            try:
                # Try to parse JSON from the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    extracted_data = json.loads(json_str)
                else:
                    extracted_data = {"raw_response": response_text}
            except json.JSONDecodeError:
                extracted_data = {"raw_response": response_text}

            return extracted_data

        except Exception as e:
            print(f"Error processing image with Ollama: {e}")
            return {"error": str(e)}

    def unload_model(self) -> None:
        """
        Unload model from memory.

        Note: For Ollama, models are managed by the daemon,
        so this method only clears the client reference.
        """
        self.client = None
        self.model = None
        print("Ollama client connection closed.")
