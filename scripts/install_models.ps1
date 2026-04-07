# PowerShell script for Windows - Model Installation
# Smartwatch LLM Service - Model Installation

$ErrorActionPreference = "Stop"

# Colors
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success { Write-ColorOutput Green $args }
function Write-Warning { Write-ColorOutput Yellow $args }
function Write-Error { Write-ColorOutput Red $args }
function Write-Info { Write-ColorOutput Cyan $args }

Write-Host "=============================================="
Write-Host "Smartwatch LLM Service - Model Installation"
Write-Host "=============================================="

# Check Python
function Test-Python {
    Write-Host ""
    Write-Host "Checking dependencies..."

    try {
        $pythonVersion = python --version 2>&1
        Write-Success "✓ Python is installed: $pythonVersion"
    }
    catch {
        Write-Error "✗ Python is not installed"
        Write-Host "Install from: https://www.python.org/downloads/"
        exit 1
    }

    # Check uv
    try {
        $uvVersion = uv --version 2>&1
        Write-Success "✓ uv is installed: $uvVersion"
    }
    catch {
        Write-Error "✗ uv is not installed"
        Write-Host "Install with: powershell -c ""irm https://astral.sh/uv/install.ps1 | iex"""
        exit 1
    }

    # Check project dependencies
    if (-not (Test-Path ".venv") -and -not (Test-Path "uv.lock")) {
        Write-Warning "⚠ Project dependencies not installed"
        Write-Host "Installing dependencies..."
        uv sync
    }
    Write-Success "✓ Project dependencies ready"
}

# Display menu
function Show-Menu {
    Write-Host ""
    Write-Host "=============================================="
    Write-Host "Select Model Installation Method"
    Write-Host "=============================================="
    Write-Host ""
    Write-Host "1) Ollama (Recommended)"
    Write-Host "   - Faster inference"
    Write-Host "   - Lower memory usage"
    Write-Host "   - Optimized for local deployment"
    Write-Host ""
    Write-Host "2) HuggingFace Direct"
    Write-Host "   - Full control over model loading"
    Write-Host "   - Access to more models"
    Write-Host "   - Requires more memory"
    Write-Host ""
    Write-Host "3) Both (Ollama + HuggingFace)"
    Write-Host ""
    Write-Host "4) List available models"
    Write-Host ""
    Write-Host "5) Exit"
    Write-Host ""
    Write-Host "=============================================="
}

# Install Ollama
function Install-Ollama {
    Write-Info "`nSetting up Ollama..."

    # Check if Ollama is installed
    try {
        $ollamaVersion = ollama --version 2>&1
        Write-Success "✓ Ollama is already installed: $ollamaVersion"
    }
    catch {
        Write-Warning "✗ Ollama is not installed"
        Write-Host ""
        Write-Host "Please download and install Ollama from:"
        Write-Host "https://ollama.ai/download"
        Write-Host ""
        $response = Read-Host "Have you installed Ollama? (y/N)"
        if ($response -ne "y") {
            Write-Host "Please install Ollama and run this script again."
            exit 1
        }
    }

    # Start Ollama (if not running)
    Write-Host ""
    Write-Host "Checking if Ollama service is running..."
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
        Write-Success "✓ Ollama service is running"
    }
    catch {
        Write-Warning "⚠ Ollama service is not running"
        Write-Host "Starting Ollama..."
        Write-Host "Please start Ollama from the Start Menu or system tray"
        Write-Host ""
        $response = Read-Host "Press Enter when Ollama is running..."
    }

    # Select models
    Write-Host ""
    Write-Host "Select models to download:"
    Write-Host ""
    Write-Host "1) phi4 only (Recommended, ~7B)"
    Write-Host "2) llava only (~7B)"
    Write-Host "3) phi4 + llava (both ~7B models)"
    Write-Host "4) Skip download"
    Write-Host ""
    $choice = Read-Host "Enter choice (1-4)"

    switch ($choice) {
        "1" {
            Write-Host "`nPulling phi4 model..."
            ollama pull phi4
            Write-Success "✓ phi4 downloaded"
        }
        "2" {
            Write-Host "`nPulling llava model..."
            ollama pull llava
            Write-Success "✓ llava downloaded"
        }
        "3" {
            Write-Host "`nPulling phi4 model..."
            ollama pull phi4
            Write-Host "`nPulling llava model..."
            ollama pull llava
            Write-Success "✓ Both models downloaded"
        }
        "4" {
            Write-Host "Skipping model download"
        }
        default {
            Write-Error "Invalid choice"
            return
        }
    }

    # List downloaded models
    Write-Host ""
    Write-Host "=============================================="
    Write-Host "Downloaded Ollama Models"
    Write-Host "=============================================="
    ollama list
}

# Install HuggingFace models
function Install-HuggingFace {
    Write-Info "`nInstalling HuggingFace models..."
    Write-Host ""
    Write-Host "Select HuggingFace models to download:"
    Write-Host ""
    Write-Host "1) phi4 (Recommended, ~7B params)"
    Write-Host "2) gemma (~2B params, smaller)"
    Write-Host "3) llava (~7B params)"
    Write-Host "4) moondream (~1.8B params, smallest)"
    Write-Host "5) All models"
    Write-Host ""
    $choice = Read-Host "Enter choice (1-5)"

    switch ($choice) {
        "1" {
            uv run python scripts/download_huggingface_model.py --model phi4
        }
        "2" {
            uv run python scripts/download_huggingface_model.py --model gemma
        }
        "3" {
            uv run python scripts/download_huggingface_model.py --model llava
        }
        "4" {
            uv run python scripts/download_huggingface_model.py --model moondream
        }
        "5" {
            uv run python scripts/download_huggingface_model.py --all
        }
        default {
            Write-Error "Invalid choice"
            return
        }
    }
}

# List models
function Show-Models {
    Write-Host ""
    Write-Host "=============================================="
    Write-Host "Available Models"
    Write-Host "=============================================="

    Write-Host ""
    Write-Info "HuggingFace Models:"
    uv run python scripts/download_huggingface_model.py --list

    Write-Host ""
    Write-Info "Ollama Models:"
    try {
        ollama list 2>&1
    }
    catch {
        Write-Host "  Ollama not installed or not running"
    }
}

# Setup .env file
function Setup-EnvFile {
    if (-not (Test-Path ".env")) {
        Write-Host ""
        Write-Host "Creating .env file from template..."
        Copy-Item ".env.example" ".env"
        Write-Success "✓ .env file created"
        Write-Host ""
        Write-Host "Update .env file to configure your model:"
        Write-Host "  LLM_MODEL_TYPE=ollama  # or phi4, gemma, etc."
        Write-Host "  LLM_MODEL_NAME=phi4    # for ollama"
    }
}

# Main execution
function Main {
    # Check dependencies
    Test-Python

    # Show menu and handle selection
    while ($true) {
        Show-Menu
        $choice = Read-Host "Enter your choice (1-5)"

        switch ($choice) {
            "1" {
                Install-Ollama
                Setup-EnvFile
                Write-Success "`n✓ Ollama setup complete!"
                break
            }
            "2" {
                Install-HuggingFace
                Setup-EnvFile
                Write-Success "`n✓ HuggingFace models installed!"
                break
            }
            "3" {
                Install-Ollama
                Write-Host ""
                Install-HuggingFace
                Setup-EnvFile
                Write-Success "`n✓ All models installed!"
                break
            }
            "4" {
                Show-Models
            }
            "5" {
                Write-Host "Exiting..."
                exit 0
            }
            default {
                Write-Error "Invalid choice. Please try again."
            }
        }
    }

    # Final instructions
    Write-Host ""
    Write-Host "=============================================="
    Write-Host "Installation Complete!"
    Write-Host "=============================================="
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host ""
    Write-Host "1. Configure your model in .env file"
    Write-Host "2. Start the service:"
    Write-Host "     uv run python main.py fastapi"
    Write-Host ""
    Write-Host "3. Or test with Gradio UI:"
    Write-Host "     uv run python main.py gradio"
    Write-Host ""
    Write-Host "=============================================="
}

# Run main function
Main
