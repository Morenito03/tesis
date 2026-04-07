#!/bin/bash
# Script to setup Ollama and download vision models

set -e  # Exit on error

echo "=============================================="
echo "Ollama Setup for Smartwatch LLM Service"
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Ollama is installed
check_ollama() {
    if command -v ollama &> /dev/null; then
        echo -e "${GREEN}✓ Ollama is installed${NC}"
        ollama --version
        return 0
    else
        echo -e "${RED}✗ Ollama is not installed${NC}"
        return 1
    fi
}

# Install Ollama based on OS
install_ollama() {
    echo ""
    echo "Installing Ollama..."
    echo ""

    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Detected Linux"
        curl -fsSL https://ollama.ai/install.sh | sh
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Detected macOS"
        if command -v brew &> /dev/null; then
            brew install ollama
        else
            echo -e "${YELLOW}Homebrew not found. Download from: https://ollama.ai/download${NC}"
            exit 1
        fi
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        echo "Detected Windows"
        echo -e "${YELLOW}Please download Ollama from: https://ollama.ai/download${NC}"
        echo "After installation, run this script again."
        exit 1
    else
        echo -e "${RED}Unsupported operating system: $OSTYPE${NC}"
        echo "Please visit: https://ollama.ai/download"
        exit 1
    fi
}

# Start Ollama service
start_ollama() {
    echo ""
    echo "Starting Ollama service..."

    # Check if already running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama service is already running${NC}"
        return 0
    fi

    # Try to start the service
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # On Linux, start as background service
        ollama serve > /dev/null 2>&1 &
        sleep 3
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # On macOS, should be started automatically
        echo -e "${YELLOW}On macOS, Ollama should start automatically${NC}"
        echo "If not running, start it manually: ollama serve"
        sleep 2
    fi

    # Verify service is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama service started successfully${NC}"
    else
        echo -e "${RED}✗ Failed to start Ollama service${NC}"
        echo "Try starting manually: ollama serve"
        exit 1
    fi
}

# Pull a vision model
pull_model() {
    local model_name=$1
    echo ""
    echo "Pulling model: $model_name"
    echo "This may take several minutes..."

    if ollama pull "$model_name"; then
        echo -e "${GREEN}✓ Model '$model_name' downloaded successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to download model '$model_name'${NC}"
        return 1
    fi
}

# List available vision models
list_available_models() {
    echo ""
    echo "=============================================="
    echo "Available Vision Models for Ollama"
    echo "=============================================="
    echo ""
    echo "1. phi4 (Recommended)"
    echo "   - Microsoft Phi-4 multimodal model"
    echo "   - Size: ~7B parameters"
    echo "   - Best quality/performance balance"
    echo ""
    echo "2. llava"
    echo "   - LLaVA 1.5 7B model"
    echo "   - Size: ~7B parameters"
    echo "   - Good vision understanding"
    echo ""
    echo "3. llava:13b"
    echo "   - LLaVA 1.5 13B model"
    echo "   - Size: ~13B parameters"
    echo "   - Better quality, slower"
    echo ""
    echo "4. bakllava"
    echo "   - BakLLaVA (LLaVA with Mistral)"
    echo "   - Size: ~7B parameters"
    echo "   - Alternative vision model"
    echo ""
    echo "=============================================="
}

# Interactive model selection
select_models() {
    echo ""
    echo "Select models to download:"
    echo ""
    echo "1) phi4 only (Recommended, ~7B)"
    echo "2) llava only (~7B)"
    echo "3) phi4 + llava (both ~7B models)"
    echo "4) All models (phi4, llava, llava:13b, bakllava)"
    echo "5) Custom selection"
    echo "6) Skip download (just setup Ollama)"
    echo ""
    read -p "Enter choice (1-6): " choice

    case $choice in
        1)
            pull_model "phi4"
            ;;
        2)
            pull_model "llava"
            ;;
        3)
            pull_model "phi4"
            pull_model "llava"
            ;;
        4)
            pull_model "phi4"
            pull_model "llava"
            pull_model "llava:13b"
            pull_model "bakllava"
            ;;
        5)
            list_available_models
            echo ""
            read -p "Enter model names (space-separated): " models
            for model in $models; do
                pull_model "$model"
            done
            ;;
        6)
            echo "Skipping model download"
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
}

# List downloaded models
list_downloaded_models() {
    echo ""
    echo "=============================================="
    echo "Downloaded Models"
    echo "=============================================="
    ollama list
    echo "=============================================="
}

# Main execution
main() {
    echo ""

    # Check if Ollama is installed
    if ! check_ollama; then
        echo ""
        read -p "Would you like to install Ollama now? (y/N): " install_choice
        if [[ $install_choice =~ ^[Yy]$ ]]; then
            install_ollama
        else
            echo "Please install Ollama manually from: https://ollama.ai/download"
            exit 1
        fi
    fi

    # Start Ollama service
    start_ollama

    # Select and download models
    select_models

    # List downloaded models
    list_downloaded_models

    # Configuration instructions
    echo ""
    echo "=============================================="
    echo "Setup Complete!"
    echo "=============================================="
    echo ""
    echo "To use Ollama with the service, configure:"
    echo ""
    echo "  export LLM_MODEL_TYPE=ollama"
    echo "  export LLM_MODEL_NAME=phi4"
    echo ""
    echo "Or add to your .env file:"
    echo ""
    echo "  LLM_MODEL_TYPE=ollama"
    echo "  LLM_MODEL_NAME=phi4"
    echo "  OLLAMA_HOST=http://localhost:11434"
    echo ""
    echo "Then start the service:"
    echo "  uv run python main.py fastapi"
    echo ""
    echo "=============================================="
}

# Run main function
main
