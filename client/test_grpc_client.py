"""Test client for gRPC service."""
import sys
import json
from pathlib import Path
from datetime import datetime
import grpc

# Import generated protobuf code
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from grpc_service.generated import smartwatch_pb2, smartwatch_pb2_grpc
except ImportError:
    print("Error: Generated protobuf files not found.")
    print("Run: python src/grpc_service/generate_protos.py")
    sys.exit(1)


class GRPCTestClient:
    """Client for testing gRPC smartwatch service."""

    def __init__(self, host: str = "localhost", port: int = 50051):
        """Initialize the gRPC test client."""
        self.address = f"{host}:{port}"
        self.channel = None
        self.stub = None

    def connect(self):
        """Connect to the gRPC server."""
        try:
            self.channel = grpc.insecure_channel(self.address)
            self.stub = smartwatch_pb2_grpc.SmartwatchServiceStub(self.channel)
            print(f"Connected to gRPC server at {self.address}")
            return True
        except Exception as e:
            print(f"Failed to connect to gRPC server: {e}")
            return False

    def disconnect(self):
        """Disconnect from the gRPC server."""
        if self.channel:
            self.channel.close()
            print("Disconnected from gRPC server")

    def process_image(
        self,
        image_path: str,
        user_id: str = "test_user",
        command: str = "extract_metrics",
        description: str = "Test extraction"
    ):
        """
        Process a smartwatch image via gRPC.

        Args:
            image_path: Path to the image file
            user_id: User ID
            command: Command to execute
            description: Description of the request

        Returns:
            Response object or None if failed
        """
        if not self.stub:
            print("Not connected to server. Call connect() first.")
            return None

        try:
            # Read image file
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            # Create request
            request = smartwatch_pb2.SmartwatchRequest(
                image=image_bytes,
                timestamp=datetime.now().isoformat(),
                user_id=user_id,
                command=command,
                description=description
            )

            # Send request
            print("Sending request to gRPC server...")
            response = self.stub.ProcessSmartwatchImage(request)

            return response

        except grpc.RpcError as e:
            print(f"gRPC Error: {e.code()}: {e.details()}")
            return None
        except FileNotFoundError:
            print(f"Image file not found: {image_path}")
            return None
        except Exception as e:
            print(f"Error processing image: {e}")
            return None


def main():
    """Main function for testing."""
    print("=" * 60)
    print("gRPC Smartwatch Service Test Client")
    print("=" * 60)

    # Initialize client
    client = GRPCTestClient(host="localhost", port=50051)

    # Connect to server
    print("\n1. Connecting to Server")
    print("-" * 60)
    if not client.connect():
        print("Failed to connect to server. Make sure the gRPC server is running.")
        print("Start server with: python -m src.grpc_service.server")
        sys.exit(1)

    # Test image processing (if image provided)
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"\n2. Processing Image: {image_path}")
        print("-" * 60)

        response = client.process_image(
            image_path=image_path,
            user_id="test_user_123",
            command="extract_all_metrics",
            description="Extract all health metrics from smartwatch"
        )

        if response:
            print(f"Success: {response.success}")
            print(f"Inference Time: {response.inference_time_ms} ms")

            if response.success:
                print(f"Extracted Data:")
                try:
                    data = json.loads(response.extracted_data)
                    print(json.dumps(data, indent=2))
                except json.JSONDecodeError:
                    print(response.extracted_data)
            else:
                print(f"Error: {response.error_message}")
        else:
            print("Failed to process image")
    else:
        print("\n2. Image Processing")
        print("-" * 60)
        print("No image provided. Usage:")
        print(f"  python {sys.argv[0]} <path_to_smartwatch_image>")

    # Disconnect
    print("\n" + "=" * 60)
    client.disconnect()
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
