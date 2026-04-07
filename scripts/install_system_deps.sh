#!/bin/bash
# =============================================================
# Install system-level dependencies for Smartwatch LLM Service
# =============================================================
# This script installs system libraries required by Python packages
# that cannot be installed via pip/uv alone.
#
# Required by:
#   - pyvips (Python) → needs libvips (C library)
#   - grpcio-tools → may need build tools
#
# Usage:
#   chmod +x scripts/install_system_deps.sh
#   sudo ./scripts/install_system_deps.sh
#
# On Lightning.ai (no sudo needed, runs as root):
#   ./scripts/install_system_deps.sh
# =============================================================

set -e

echo "=============================================="
echo "Installing system dependencies"
echo "=============================================="

# Detect package manager
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
elif command -v apk &> /dev/null; then
    PKG_MANAGER="apk"
elif command -v pacman &> /dev/null; then
    PKG_MANAGER="pacman"
else
    echo "Error: No supported package manager found (apt, dnf, yum, apk, pacman)"
    echo "Please install libvips manually for your system."
    exit 1
fi

echo "Detected package manager: $PKG_MANAGER"
echo ""

# Check if we need sudo
SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    if command -v sudo &> /dev/null; then
        SUDO="sudo"
        echo "Running with sudo..."
    else
        echo "Error: Not running as root and sudo is not available."
        echo "Please run this script as root or install sudo."
        exit 1
    fi
fi

case $PKG_MANAGER in
    apt)
        echo "→ Updating package lists..."
        $SUDO apt-get update -qq

        echo "→ Installing libvips and build dependencies..."
        $SUDO apt-get install -y -qq \
            libvips42 \
            libvips-dev \
            libvips-tools \
            build-essential \
            2>/dev/null || {
                # Fallback: on some Ubuntu/Debian versions the package is just 'libvips'
                echo "→ Trying alternative package names..."
                $SUDO apt-get install -y -qq \
                    libvips \
                    libvips-dev \
                    build-essential \
                    2>/dev/null || {
                        echo "→ Trying minimal install..."
                        $SUDO apt-get install -y -qq libvips-dev 2>/dev/null
                    }
            }
        ;;
    dnf)
        echo "→ Installing libvips..."
        $SUDO dnf install -y vips vips-devel
        ;;
    yum)
        echo "→ Installing libvips..."
        $SUDO yum install -y vips vips-devel
        ;;
    apk)
        echo "→ Installing libvips..."
        $SUDO apk add --no-cache vips vips-dev
        ;;
    pacman)
        echo "→ Installing libvips..."
        $SUDO pacman -S --noconfirm libvips
        ;;
esac

# Verify installation
echo ""
echo "→ Verifying libvips installation..."
if ldconfig -p 2>/dev/null | grep -q libvips; then
    VIPS_VERSION=$(vips --version 2>/dev/null || echo "installed (version unknown)")
    echo "✅ libvips found: $VIPS_VERSION"
elif command -v vips &> /dev/null; then
    VIPS_VERSION=$(vips --version 2>/dev/null || echo "installed")
    echo "✅ libvips found: $VIPS_VERSION"
elif [ -f /usr/lib/libvips.so ] || [ -f /usr/lib/x86_64-linux-gnu/libvips.so.42 ] || [ -f /usr/lib64/libvips.so ]; then
    echo "✅ libvips shared library found"
else
    echo "⚠️  libvips may not be properly installed. If pyvips still fails, try:"
    echo "    apt-get install libvips-dev  (Debian/Ubuntu)"
    echo "    dnf install vips-devel       (Fedora/RHEL)"
fi

echo ""
echo "=============================================="
echo "System dependencies installed successfully!"
echo "=============================================="
echo ""
echo "Next: run 'uv sync' to install Python dependencies."
