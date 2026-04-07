"""Test client for FastAPI service."""
import requests
import sys
from pathlib import Path
from datetime import datetime


class FastAPITestClient:
    """Client for testing FastAPI smartwatch service."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the test client."""
        self.base_url = base_url

    def health_check(self):
        """Check if the service is healthy."""
        try:
            response = requests.get(f"{self.base_url}/")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Health check failed: {e}")
            return None

    def list_models(self):
        """List available models."""
        try:
            response = requests.get(f"{self.base_url}/models")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to list models: {e}")
            return None

    def process_image(
        self,
        image_path: str,
        user_id: str = "test_user",
        command: str = "extract_metrics",
        description: str = "Test extraction"
    ):
        """
        Process a smartwatch image.

        Args:
            image_path: Path to the image file
            user_id: User ID
            command: Command to execute
            description: Description of the request

        Returns:
            Response dictionary or None if failed
        """
        try:
            # Prepare the image file
            with open(image_path, "rb") as image_file:
                files = {"image": image_file}
                data = {
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "command": command,
                    "description": description
                }

                # Send request
                response = requests.post(
                    f"{self.base_url}/process",
                    files=files,
                    data=data
                )
                response.raise_for_status()
                return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error processing image: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None
        except FileNotFoundError:
            print(f"Image file not found: {image_path}")
            return None


def main():
    """Main function for testing."""
    # Initialize client
    client = FastAPITestClient()

    print("=" * 60)
    print("FastAPI Smartwatch Service Test Client")
    print("=" * 60)

    # Health check
    print("\n1. Health Check")
    print("-" * 60)
    health = client.health_check()
    if health:
        print(f"Status: {health.get('status')}")
        print(f"Model Loaded: {health.get('model_loaded')}")
        print(f"Model Name: {health.get('model_name')}")
    else:
        print("Service is not available. Make sure the server is running.")
        sys.exit(1)

    # List models
    print("\n2. Available Models")
    print("-" * 60)
    models = client.list_models()
    if models:
        print(f"Available models: {models.get('available_models')}")
        print(f"Current model: {models.get('current_model')}")

    # Test image processing (if image provided)
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"\n3. Processing Image: {image_path}")
        print("-" * 60)

        result = client.process_image(
            image_path=image_path,
            user_id="test_user_123",
            command="extract_all_metrics",
            description="Extract all health metrics from smartwatch"
        )

        if result:
            print(f"Success: {result.get('success')}")
            print(f"Inference Time: {result.get('inference_time_ms')} ms")
            print(f"Extracted Data:")
            import json
            print(json.dumps(result.get('extracted_data'), indent=2))

            if result.get('error_message'):
                print(f"Error: {result.get('error_message')}")
    else:
        print("\n3. Image Processing")
        print("-" * 60)
        print("No image provided. Usage:")
        print(f"  python {sys.argv[0]} <path_to_smartwatch_image>")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
