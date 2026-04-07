"""Base class for multimodal LLM models."""
from abc import ABC, abstractmethod
from typing import Dict, Any
from PIL import Image


class BaseLLM(ABC):
    """Abstract base class for multimodal LLM implementations."""

    def __init__(self, model_name: str, device: str = "cpu"):
        """
        Initialize the LLM model.

        Args:
            model_name: Name/path of the model
            device: Device to run inference on (cpu/cuda)
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.processor = None

    @abstractmethod
    def load_model(self) -> None:
        """Load the model and processor into memory."""
        pass

    @abstractmethod
    def process_image(
        self,
        image: Image.Image,
        prompt: str,
        system_prompt: str = ""
    ) -> Dict[str, Any]:
        """
        Process an image with a prompt and return extracted data.

        Args:
            image: PIL Image object
            prompt: User prompt for the model
            system_prompt: System prompt with instructions

        Returns:
            Dictionary with extracted data from the image
        """
        pass

    def unload_model(self) -> None:
        """Unload model from memory to free resources."""
        if self.model is not None:
            del self.model
            del self.processor
            self.model = None
            self.processor = None

            # Clear CUDA cache if using GPU
            if self.device.startswith("cuda"):
                import torch
                torch.cuda.empty_cache()
