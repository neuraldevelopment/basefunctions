#!/bin/bash
# =============================================================================
# Installation script for dbadmin CLI tool
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_NAME="dbadmin"
INSTALL_DIR="$HOME/.bin"
COMPLETION_DIR="$HOME/.zsh/completions"
ZSHRC="$HOME/.zshrc"

echo "🚀 Installing dbadmin CLI tool..."

# Create directories
echo "📁 Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$COMPLETION_DIR"

# Copy dbadmin script
echo "📄 Installing dbadmin script..."
if [ -f "dbadmin" ]; then
    cp dbadmin "$INSTALL_DIR/$SCRIPT_NAME"
    chmod +x "$INSTALL_DIR/$SCRIPT_NAME"
    echo -e "${GREEN}✓${NC} Installed $SCRIPT_NAME to $INSTALL_DIR"
else
    echo -e "${RED}✗${NC} dbadmin script not found in current directory"
    exit 1
fi

# Copy completion script
echo "🔧 Installing zsh completion..."
if [ -f "_dbadmin" ]; then
    cp _dbadmin "$COMPLETION_DIR/"
    echo -e "${GREEN}✓${NC} Installed completion to $COMPLETION_DIR"
else
    echo -e "${YELLOW}⚠${NC} Completion script not found, skipping..."
fi

# Check if ~/.bin is in PATH
if [[ ":$PATH:" != *":$HOME/.bin:"* ]]; then
    echo "📝 Adding ~/.bin to PATH..."
    
    # Add to .zshrc if it exists
    if [ -f "$ZSHRC" ]; then
        echo "" >> "$ZSHRC"
        echo "# dbadmin CLI tool" >> "$ZSHRC"
        echo 'export PATH="$HOME/.bin:$PATH"' >> "$ZSHRC"
        echo -e "${GREEN}✓${NC} Added ~/.bin to PATH in $ZSHRC"
    else
        echo -e "${YELLOW}⚠${NC} No .zshrc found. Please add ~/.bin to your PATH manually:"
        echo "    export PATH=\"\$HOME/.bin:\$PATH\""
    fi
fi

# Setup completion in .zshrc
if [ -f "$ZSHRC" ]; then
    if ! grep -q "$COMPLETION_DIR" "$ZSHRC"; then
        echo "🔧 Setting up zsh completion..."
        echo "" >> "$ZSHRC"
        echo "# dbadmin completion" >> "$ZSHRC"
        echo "fpath=($COMPLETION_DIR \$fpath)" >> "$ZSHRC"
        echo "autoload -U compinit && compinit" >> "$ZSHRC"
        echo -e "${GREEN}✓${NC} Added completion setup to $ZSHRC"
    else
        echo -e "${GREEN}✓${NC} Completion already configured in $ZSHRC"
    fi
fi

# Install templates
echo "📦 Installing default templates..."
if command -v "$INSTALL_DIR/$SCRIPT_NAME" >/dev/null 2>&1; then
    if "$INSTALL_DIR/$SCRIPT_NAME" templates install; then
        echo -e "${GREEN}✓${NC} Templates installed successfully"
    else
        echo -e "${YELLOW}⚠${NC} Template installation failed, you can install them later with: dbadmin templates install"
    fi
else
    echo -e "${YELLOW}⚠${NC} Cannot test dbadmin installation, please install templates manually later"
fi

echo ""
echo -e "${GREEN}🎉 Installation complete!${NC}"
echo ""
echo "To get started:"
echo "  1. Restart your shell or run: source ~/.zshrc"
echo "  2. Test the installation: dbadmin --help"
echo "  3. Create your first instance: dbadmin create postgres mydb"
echo ""
echo "Available commands:"
echo "  dbadmin create <type> <name>     # Create new instance"
echo "  dbadmin list                     # List all instances"
echo "  dbadmin start <name>             # Start instance"
echo "  dbadmin stop <name>              # Stop instance"
echo "  dbadmin status <name>            # Check status"
echo "  dbadmin delete <name>            # Delete instance"
echo ""
echo "Tab completion is enabled - try typing 'dbadmin ' and press TAB!"