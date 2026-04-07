"""Script to generate Python code from Protocol Buffers definitions."""
import subprocess
import sys
from pathlib import Path


def generate_grpc_code():
    """Generate gRPC Python code from .proto files."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    protos_dir = project_root / "src" / "grpc_service" / "protos"
    output_dir = project_root / "src" / "grpc_service" / "generated"

    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)

    # Create __init__.py in generated directory
    init_file = output_dir / "__init__.py"
    init_file.touch()

    # Find all .proto files
    proto_files = list(protos_dir.glob("*.proto"))

    if not proto_files:
        print("No .proto files found!")
        return False

    # Generate Python code for each .proto file
    for proto_file in proto_files:
        print(f"Generating code for {proto_file.name}...")

        cmd = [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"--proto_path={protos_dir}",
            f"--python_out={output_dir}",
            f"--grpc_python_out={output_dir}",
            str(proto_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error generating code for {proto_file.name}:")
            print(result.stderr)
            return False

        print(f"Successfully generated code for {proto_file.name}")

    print("\nAll proto files processed successfully!")
    return True


if __name__ == "__main__":
    success = generate_grpc_code()
    sys.exit(0 if success else 1)
