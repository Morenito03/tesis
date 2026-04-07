"""gRPC server for smartwatch image processing."""
import time
import io
import json
from concurrent import futures
import grpc
from PIL import Image

# Import generated protobuf code
# Note: These imports will work after running generate_protos.py
try:
    from .generated import smartwatch_pb2, smartwatch_pb2_grpc
except ImportError:
    print("Warning: Generated protobuf files not found.")
    print("Run: python src/grpc_service/generate_protos.py")
    smartwatch_pb2 = None
    smartwatch_pb2_grpc = None

from ..llm.factory import LLMFactory


# System prompt for the LLM
SYSTEM_PROMPT = """You are an AI assistant specialized in extracting data from smartwatch screenshots.
Your task is to analyze the image and extract all relevant information such as:
- Heart rate
- Steps count
- Calories burned
- Distance traveled
- Active minutes
- Sleep data
- Any other metrics visible

Return the data in a valid JSON format with clear key-value pairs.
Example: {"heart_rate": "72 bpm", "steps": "8543", "calories": "450 kcal"}
"""


class SmartwatchServicer:
    """gRPC servicer for smartwatch image processing."""

    def __init__(self):
        """Initialize the servicer with an LLM instance."""
        self.llm = None
        self._load_model()

    def _load_model(self):
        """Load the LLM model."""
        try:
            print("Loading LLM model for gRPC service...")
            self.llm = LLMFactory.create_llm(
                model_type="phi4",
                device="cpu"
            )
            self.llm.load_model()
            print("LLM model loaded successfully for gRPC")
        except Exception as e:
            print(f"Error loading LLM model: {e}")

    def ProcessSmartwatchImage(self, request, context):
        """Process smartwatch image via gRPC."""
        if smartwatch_pb2 is None:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("gRPC service not properly initialized")
            return smartwatch_pb2.SmartwatchResponse()

        # Load model if not already loaded
        if self.llm is None or self.llm.model is None:
            try:
                self._load_model()
            except Exception as e:
                return smartwatch_pb2.SmartwatchResponse(
                    success=False,
                    error_message=f"Failed to load model: {str(e)}",
                    inference_time_ms=0
                )

        try:
            # Convert bytes to PIL Image
            image_bytes = request.image
            pil_image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if necessary
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

            # Construct user prompt
            user_prompt = f"""Command: {request.command}
Description: {request.description}
User: {request.user_id}
Timestamp: {request.timestamp}

Analyze this smartwatch screenshot and extract all visible data.
Return the extracted data as a JSON object."""

            # Start inference timer
            start_time = time.time()

            # Process image with LLM
            extracted_data = self.llm.process_image(
                image=pil_image,
                prompt=user_prompt,
                system_prompt=SYSTEM_PROMPT
            )

            # Calculate inference time
            inference_time_ms = int((time.time() - start_time) * 1000)

            # Convert extracted data to JSON string
            json_data = json.dumps(extracted_data, ensure_ascii=False)

            # Check for errors
            if "error" in extracted_data:
                return smartwatch_pb2.SmartwatchResponse(
                    extracted_data=json_data,
                    inference_time_ms=inference_time_ms,
                    success=False,
                    error_message=extracted_data["error"]
                )

            return smartwatch_pb2.SmartwatchResponse(
                extracted_data=json_data,
                inference_time_ms=inference_time_ms,
                success=True,
                error_message=""
            )

        except Exception as e:
            return smartwatch_pb2.SmartwatchResponse(
                success=False,
                error_message=f"Error processing image: {str(e)}",
                inference_time_ms=0
            )


def serve(port: int = 50051):
    """Start the gRPC server."""
    if smartwatch_pb2_grpc is None:
        print("Error: Cannot start gRPC server without generated protobuf files")
        print("Run: python src/grpc_service/generate_protos.py")
        return

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    smartwatch_pb2_grpc.add_SmartwatchServiceServicer_to_server(
        SmartwatchServicer(),
        server
    )

    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"gRPC server started on port {port}")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nShutting down gRPC server...")
        server.stop(0)


if __name__ == "__main__":
    serve()
