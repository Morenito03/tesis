"""Gradio interface for testing FastAPI and gRPC services."""
import gradio as gr
import requests
import io
import json
import os
from datetime import datetime
from PIL import Image
import grpc

# Import gRPC generated code
try:
    from ..grpc_service.generated import smartwatch_pb2, smartwatch_pb2_grpc
    GRPC_AVAILABLE = True
except ImportError:
    print("Warning: gRPC protobuf files not found. gRPC testing will be disabled.")
    print("Run: python main.py generate-protos")
    GRPC_AVAILABLE = False


def test_fastapi(image, timestamp, user_id, command, description, fastapi_url):
    """
    Test FastAPI service.

    Args:
        image: PIL Image object
        timestamp: Request timestamp
        user_id: User ID
        command: Command
        description: Description
        fastapi_url: FastAPI server URL

    Returns:
        Formatted response string
    """
    try:
        if image is None:
            return "Error: Please upload an image"

        # Convert PIL Image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        # Prepare form data
        files = {'image': ('image.png', img_byte_arr, 'image/png')}
        data = {
            'timestamp': timestamp,
            'user_id': user_id,
            'command': command,
            'description': description
        }

        # Normalize URL: remove trailing slash
        base_url = fastapi_url.rstrip("/")

        # Verify server is reachable before sending image
        try:
            health = requests.get(f"{base_url}/", timeout=5)
            if health.status_code != 200 or "model_loaded" not in health.text:
                return (
                    f"Error: The server at {base_url} is not the FastAPI service.\n"
                    f"Response: {health.text[:200]}\n\n"
                    f"Make sure the FastAPI server is running:\n"
                    f"  uv run python main.py fastapi\n\n"
                    f"If port 8000 is taken (e.g. on Lightning.ai), set a different port in .env:\n"
                    f"  FASTAPI_PORT=8001\n"
                    f"Then update the URL above to http://localhost:8001"
                )
            # Check if model is still loading
            health_data = health.json()
            if health_data.get("model_loading") and not health_data.get("model_loaded"):
                return (
                    f"⏳ The model is still loading, please wait...\n\n"
                    f"Model: {health_data.get('model_name', 'Unknown')}\n"
                    f"Check the 'Model Status' indicator above and try again\n"
                    f"once it shows ✅ Model ready."
                )
        except requests.exceptions.ConnectionError:
            # Detect if user is using a Lightning.ai public URL instead of localhost
            is_cloud_url = ("cloudspaces" in base_url or "litng.ai" in base_url
                           or "lightning.ai" in base_url)
            _port = os.getenv("FASTAPI_PORT", "8001")

            if is_cloud_url:
                return (
                    f"Error: Could not connect to FastAPI server at {base_url}\n\n"
                    f"⚠️  You are using a Lightning.ai public URL. On Lightning.ai,\n"
                    f"port 8000 is RESERVED by the platform and cannot be used for FastAPI.\n\n"
                    f"Fix:\n"
                    f"1. Set FASTAPI_PORT=8001 in your .env file\n"
                    f"2. Restart the FastAPI server: uv run python main.py fastapi\n"
                    f"3. Change the URL above to: http://localhost:{_port}\n"
                    f"   (Gradio and FastAPI run on the same machine, use localhost)\n"
                )
            else:
                return (
                    f"Error: Could not connect to FastAPI server at {base_url}\n\n"
                    f"Start the server in a separate terminal:\n"
                    f"  uv run python main.py fastapi\n\n"
                    f"If port 8000 is taken (e.g. on Lightning.ai), set in .env:\n"
                    f"  FASTAPI_PORT={_port}\n"
                    f"Then update the URL above to http://localhost:{_port}"
                )

        # Make request to FastAPI
        response = requests.post(
            f"{base_url}/process",
            files=files,
            data=data,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            return format_response(result, "FastAPI")
        else:
            return f"Error: HTTP {response.status_code}\n{response.text}"

    except requests.exceptions.ConnectionError:
        return f"Error: Could not connect to FastAPI server at {fastapi_url}\nMake sure the server is running: uv run python main.py fastapi"
    except Exception as e:
        return f"Error calling FastAPI: {str(e)}"


def test_grpc(image, timestamp, user_id, command, description, grpc_host, grpc_port):
    """
    Test gRPC service.

    Args:
        image: PIL Image object
        timestamp: Request timestamp
        user_id: User ID
        command: Command
        description: Description
        grpc_host: gRPC server host
        grpc_port: gRPC server port

    Returns:
        Formatted response string
    """
    if not GRPC_AVAILABLE:
        return "Error: gRPC protobuf files not generated.\nRun: uv run python main.py generate-protos"

    try:
        if image is None:
            return "Error: Please upload an image"

        # Convert PIL Image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        image_bytes = img_byte_arr.getvalue()

        # Create gRPC channel and stub
        channel = grpc.insecure_channel(f"{grpc_host}:{grpc_port}")
        stub = smartwatch_pb2_grpc.SmartwatchServiceStub(channel)

        # Create request
        request = smartwatch_pb2.SmartwatchRequest(
            image=image_bytes,
            timestamp=timestamp,
            user_id=user_id,
            command=command,
            description=description
        )

        # Make gRPC call
        response = stub.ProcessSmartwatchImage(request, timeout=60)

        # Convert response to dict
        result = {
            'success': response.success,
            'extracted_data': json.loads(response.extracted_data) if response.extracted_data else {},
            'inference_time_ms': response.inference_time_ms,
            'error_message': response.error_message if response.error_message else None
        }

        channel.close()
        return format_response(result, "gRPC")

    except grpc.RpcError as e:
        return f"Error: Could not connect to gRPC server at {grpc_host}:{grpc_port}\nMake sure the server is running: uv run python main.py grpc\nDetails: {e.details()}"
    except Exception as e:
        return f"Error calling gRPC: {str(e)}"


def format_response(result, service_type):
    """
    Format the response for display.

    Args:
        result: Response dictionary
        service_type: Type of service (FastAPI or gRPC)

    Returns:
        Formatted string
    """
    output = f"=== {service_type} Response ===\n\n"
    output += f"Success: {result.get('success', False)}\n"
    output += f"Inference Time: {result.get('inference_time_ms', 0)} ms\n\n"

    if result.get('error_message'):
        output += f"Error Message: {result['error_message']}\n\n"

    output += "Extracted Data:\n"
    extracted_data = result.get('extracted_data', {})
    if isinstance(extracted_data, dict):
        output += json.dumps(extracted_data, indent=2, ensure_ascii=False)
    else:
        output += str(extracted_data)

    return output


def _check_model_status(fastapi_url):
    """
    Check the model loading status from the FastAPI health endpoint.

    Args:
        fastapi_url: FastAPI server URL

    Returns:
        Formatted status string with emoji indicator
    """
    try:
        base_url = fastapi_url.rstrip("/")
        resp = requests.get(f"{base_url}/", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            model_name = data.get("model_name", "Unknown")
            if data.get("model_loaded"):
                return f"✅ **Model ready** — `{model_name}` loaded and ready for inference"
            elif data.get("model_loading"):
                return f"⏳ **Loading model...** — `{model_name}` is being loaded, please wait"
            else:
                return "⚪ **Model not loaded** — Will load on first request"
        else:
            return f"⚠️ **Server error** — HTTP {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return "🔴 **Server offline** — FastAPI is not running"
    except Exception as e:
        return f"⚠️ **Error** — {str(e)}"


def create_interface():
    """Create and configure the Gradio interface."""

    # Default values
    default_timestamp = datetime.now().isoformat()
    default_user_id = "user123"
    default_command = "extract_metrics"
    default_description = "Extract all visible health metrics from this smartwatch screenshot"

    with gr.Blocks(title="Smartwatch LLM Service - Tester") as demo:
        gr.Markdown(
            """
            # 🔬 Smartwatch LLM Service Tester

            Upload a smartwatch screenshot and test both FastAPI and gRPC services.
            Make sure the respective servers are running before testing:
            - FastAPI: `uv run python main.py fastapi`
            - gRPC: `uv run python main.py grpc`
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Input")

                # Image input
                image_input = gr.Image(
                    label="Smartwatch Screenshot",
                    type="pil",
                    height=300
                )

                # Metadata inputs
                timestamp_input = gr.Textbox(
                    label="Timestamp",
                    value=default_timestamp,
                    placeholder="ISO format timestamp"
                )

                user_id_input = gr.Textbox(
                    label="User ID",
                    value=default_user_id,
                    placeholder="User identifier"
                )

                command_input = gr.Textbox(
                    label="Command",
                    value=default_command,
                    placeholder="Command to execute"
                )

                description_input = gr.Textbox(
                    label="Description",
                    value=default_description,
                    placeholder="Task description",
                    lines=3
                )

            with gr.Column(scale=1):
                gr.Markdown("### Service Configuration")

                # Service selection
                service_type = gr.Radio(
                    choices=["FastAPI", "gRPC"],
                    label="Service Type",
                    value="FastAPI"
                )

                # FastAPI configuration
                with gr.Group(visible=True) as fastapi_config:
                    gr.Markdown("#### FastAPI Configuration")
                    _fastapi_port = os.getenv("FASTAPI_PORT", "8000")

                    # Auto-detect correct FastAPI URL
                    # On Lightning.ai, port 8000 is reserved; use localhost for internal calls
                    _default_fastapi_url = f"http://localhost:{_fastapi_port}"

                    fastapi_url = gr.Textbox(
                        label="FastAPI URL",
                        value=_default_fastapi_url,
                        placeholder="http://localhost:8001",
                        info="Use http://localhost:<port>. On Lightning.ai, avoid port 8000 (reserved)."
                    )

                # gRPC configuration
                with gr.Group(visible=False) as grpc_config:
                    gr.Markdown("#### gRPC Configuration")
                    grpc_host = gr.Textbox(
                        label="gRPC Host",
                        value="localhost",
                        placeholder="localhost"
                    )
                    grpc_port = gr.Number(
                        label="gRPC Port",
                        value=50051,
                        precision=0
                    )

                # Test button
                test_button = gr.Button("Test Service", variant="primary", size="lg")

                # Model status indicator
                gr.Markdown("### Model Status")
                model_status = gr.Markdown(
                    value="⏳ **Checking model status...**"
                )
                refresh_status_btn = gr.Button("🔄 Refresh Status", size="sm")

                # Output
                gr.Markdown("### Response")
                output_text = gr.Textbox(
                    label="Service Response",
                    lines=15,
                    max_lines=20,
                )

        # Toggle visibility based on service type
        def update_config_visibility(service):
            if service == "FastAPI":
                return gr.update(visible=True), gr.update(visible=False)
            else:
                return gr.update(visible=False), gr.update(visible=True)

        service_type.change(
            fn=update_config_visibility,
            inputs=[service_type],
            outputs=[fastapi_config, grpc_config]
        )

        # Model status refresh handler
        def refresh_model_status(url):
            return _check_model_status(url)

        refresh_status_btn.click(
            fn=refresh_model_status,
            inputs=[fastapi_url],
            outputs=[model_status]
        )

        # Auto-refresh model status every 5 seconds using gr.Timer
        status_timer = gr.Timer(value=5)
        status_timer.tick(
            fn=refresh_model_status,
            inputs=[fastapi_url],
            outputs=[model_status]
        )

        # Also check on page load
        demo.load(
            fn=refresh_model_status,
            inputs=[fastapi_url],
            outputs=[model_status]
        )

        # Handle test button click
        def handle_test(service, image, timestamp, user_id, command, description,
                       fastapi_url, grpc_host, grpc_port):
            if service == "FastAPI":
                return test_fastapi(image, timestamp, user_id, command, description, fastapi_url)
            else:
                return test_grpc(image, timestamp, user_id, command, description,
                               grpc_host, int(grpc_port))

        test_button.click(
            fn=handle_test,
            inputs=[
                service_type, image_input, timestamp_input, user_id_input,
                command_input, description_input, fastapi_url, grpc_host, grpc_port
            ],
            outputs=[output_text]
        )

        # Examples
        gr.Markdown("### Tips")
        gr.Markdown(
            """
            - Upload a clear screenshot of a smartwatch display
            - The LLM will extract metrics like heart rate, steps, calories, etc.
            - Compare response times between FastAPI and gRPC
            - Make sure servers are running before testing
            """
        )

    return demo


def launch(server_name="0.0.0.0", server_port=7860, share=False):
    """
    Launch the Gradio interface.

    Args:
        server_name: Server host
        server_port: Server port
        share: Whether to create a public link
    """
    demo = create_interface()
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        theme=gr.themes.Soft()
    )


if __name__ == "__main__":
    launch()
