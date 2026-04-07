#!/bin/bash
# Master script to install models for Smartwatch LLM Service

set -e  # Exit on error

# Navigate to project root (one directory up from scripts/)
cd "$(dirname "$0")/.."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=============================================="
echo "Smartwatch LLM Service - Model Installation"
echo "=============================================="

# Check dependencies
check_dependencies() {
    echo ""
    echo "Checking dependencies..."

    # Check Python
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        echo -e "${RED}✗ Python is not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python is installed${NC}"

    # Check uv
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}✗ uv is not installed${NC}"
        echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    echo -e "${GREEN}✓ uv is installed${NC}"

    # Check if project dependencies are installed
    if [ ! -d ".venv" ] && [ ! -f "uv.lock" ]; then
        echo -e "${YELLOW}⚠ Project dependencies not installed${NC}"
        echo "Installing dependencies..."
        uv sync
    fi
    echo -e "${GREEN}✓ Project dependencies ready${NC}"
}

# Display menu
show_menu() {
    echo ""
    echo "=============================================="
    echo "Select Model Installation Method"
    echo "=============================================="
    echo ""
    echo "1) Ollama (Recommended)"
    echo "   - Faster inference"
    echo "   - Lower memory usage"
    echo "   - Optimized for local deployment"
    echo "   - Easy model management"
    echo ""
    echo "2) HuggingFace Direct"
    echo "   - Full control over model loading"
    echo "   - Access to more models"
    echo "   - Requires more memory"
    echo "   - Slower first load"
    echo ""
    echo "3) Both (Ollama + HuggingFace)"
    echo "   - Maximum flexibility"
    echo "   - Requires more disk space"
    echo ""
    echo "4) List available models"
    echo ""
    echo "5) Exit"
    echo ""
    echo "=============================================="
}

# Install Ollama models
install_ollama() {
    echo ""
    echo -e "${BLUE}Setting up Ollama...${NC}"
    bash scripts/setup_ollama.sh
}

# Install HuggingFace models
install_huggingface() {
    echo ""
    echo -e "${BLUE}Installing HuggingFace models...${NC}"
    echo ""
    echo "Select HuggingFace models to download:"
    echo ""
    echo "1) phi4 (Recommended, ~7B params)"
    echo "2) gemma (~2B params, smaller)"
    echo "3) gemma3n (~2B params, Gemma 3n)"
    echo "4) llava (~7B params)"
    echo "5) moondream (~1.8B params, smallest)"
    echo "6) qwen2vl (~2B params, Qwen2-VL)"
    echo "7) All models"
    echo "8) Custom model"
    echo ""
    read -p "Enter choice (1-8): " hf_choice

    case $hf_choice in
        1)
            uv run python scripts/download_huggingface_model.py --model phi4
            ;;
        2)
            uv run python scripts/download_huggingface_model.py --model gemma
            ;;
        3)
            uv run python scripts/download_huggingface_model.py --model gemma3n
            ;;
        4)
            uv run python scripts/download_huggingface_model.py --model llava
            ;;
        5)
            uv run python scripts/download_huggingface_model.py --model moondream
            ;;
        6)
            uv run python scripts/download_huggingface_model.py --model qwen2vl
            ;;
        7)
            uv run python scripts/download_huggingface_model.py --all
            ;;
        8)
            echo ""
            uv run python scripts/download_huggingface_model.py --list
            echo ""
            read -p "Enter model type: " model_type
            uv run python scripts/download_huggingface_model.py --model "$model_type"
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            return 1
            ;;
    esac
}

# List models
list_models() {
    echo ""
    echo "=============================================="
    echo "Available Models"
    echo "=============================================="

    echo ""
    echo -e "${BLUE}HuggingFace Models:${NC}"
    uv run python scripts/download_huggingface_model.py --list

    echo ""
    echo -e "${BLUE}Ollama Models:${NC}"
    if command -v ollama &> /dev/null; then
        ollama list 2>/dev/null || echo "  No models installed or Ollama not running"
    else
        echo "  Ollama not installed"
    fi

    echo ""
}

# Create .env file if it doesn't exist
setup_env_file() {
    if [ ! -f ".env" ]; then
        echo ""
        echo "Creating .env file from template..."
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created${NC}"
        echo ""
        echo "Update .env file to configure your model:"
        echo "  LLM_MODEL_TYPE=ollama  # or phi4, gemma, etc."
        echo "  LLM_MODEL_NAME=phi4    # for ollama"
    fi
}

# Main execution
main() {
    # Check dependencies first
    check_dependencies

    # Show menu and handle selection
    while true; do
        show_menu
        read -p "Enter your choice (1-5): " choice

        case $choice in
            1)
                install_ollama
                setup_env_file
                echo ""
                echo -e "${GREEN}✓ Ollama setup complete!${NC}"
                break
                ;;
            2)
                install_huggingface
                setup_env_file
                echo ""
                echo -e "${GREEN}✓ HuggingFace models installed!${NC}"
                break
                ;;
            3)
                install_ollama
                echo ""
                install_huggingface
                setup_env_file
                echo ""
                echo -e "${GREEN}✓ All models installed!${NC}"
                break
                ;;
            4)
                list_models
                ;;
            5)
                echo "Exiting..."
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice. Please try again.${NC}"
                ;;
        esac
    done

    # Final instructions
    echo ""
    echo "=============================================="
    echo "Installation Complete!"
    echo "=============================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Configure your model in .env file"
    echo "2. Start the service:"
    echo "     uv run python main.py fastapi"
    echo ""
    echo "3. Or test with Gradio UI:"
    echo "     uv run python main.py gradio"
    echo ""
    echo "=============================================="
}

# Run main function
main
