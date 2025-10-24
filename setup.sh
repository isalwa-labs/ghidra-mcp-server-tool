#!/bin/bash
# Ghidra MCP Server Setup Script
# Author: Isaac Isalwa

set -e  # Exit on error

echo "========================================="
echo "  Ghidra MCP Server Setup"
echo "  Student-Friendly Installation"
echo "========================================="
echo ""

# Check Python version
echo "[1/5] Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✅ Found Python $PYTHON_VERSION"
echo ""

# Install Python dependencies
echo "[2/5] Installing Python dependencies..."
pip3 install mcp || {
    echo "❌ Failed to install MCP. Try: pip3 install --user mcp"
    exit 1
}
echo "✅ MCP installed successfully"
echo ""

# Check for required system tools
echo "[3/5] Checking system tools..."

check_tool() {
    if command -v $1 &> /dev/null; then
        echo "  ✅ $1 found"
        return 0
    else
        echo "  ⚠️  $1 not found"
        return 1
    fi
}

MISSING_TOOLS=0

check_tool "file" || MISSING_TOOLS=$((MISSING_TOOLS + 1))
check_tool "strings" || MISSING_TOOLS=$((MISSING_TOOLS + 1))
check_tool "readelf" || MISSING_TOOLS=$((MISSING_TOOLS + 1))
check_tool "nm" || MISSING_TOOLS=$((MISSING_TOOLS + 1))

if [ $MISSING_TOOLS -gt 0 ]; then
    echo ""
    echo "⚠️  Some tools are missing. Install them with:"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  sudo apt-get install binutils file"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install binutils"
    fi
    
    echo ""
    echo "The server will work but with limited functionality."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Create workspace directory
echo "[4/5] Creating workspace directory..."
WORKSPACE="$HOME/.ghidra_mcp_workspace"
mkdir -p "$WORKSPACE"
echo "✅ Workspace created at: $WORKSPACE"
echo ""

# Get script path
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/ghidra_mcp_server.py"

# Detect OS and configure Claude Desktop
echo "[5/5] Claude Desktop configuration..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CONFIG_DIR="$HOME/.config/Claude"
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    CONFIG_DIR="$APPDATA/Claude"
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
else
    echo "⚠️  Unknown OS. Please configure manually."
    CONFIG_FILE=""
fi

if [ -n "$CONFIG_FILE" ]; then
    mkdir -p "$CONFIG_DIR"
    
    # Create or update config
    if [ -f "$CONFIG_FILE" ]; then
        echo "⚠️  Config file already exists: $CONFIG_FILE"
        echo "Please add this configuration manually:"
    else
        echo "Creating new config file..."
    fi
    
    cat << EOF

Add this to your Claude Desktop config:

{
  "mcpServers": {
    "ghidra-mcp": {
      "command": "python3",
      "args": [
        "$SCRIPT_PATH"
      ]
    }
  }
}

Config file location: $CONFIG_FILE
EOF

    read -p "Would you like me to create/update this config? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "$CONFIG_FILE" ]; then
            cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
            echo "✅ Backup created: $CONFIG_FILE.backup"
        fi
        
        cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "ghidra-mcp": {
      "command": "python3",
      "args": [
        "$SCRIPT_PATH"
      ]
    }
  }
}
EOF
        echo "✅ Config file created!"
    fi
fi

echo ""
echo "========================================="
echo "  🎉 Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Make sure ghidra_mcp_server.py is in this directory"
echo "2. Restart Claude Desktop completely"
echo "3. Look for the 🔌 icon in Claude Desktop (bottom right)"
echo "4. Try asking Claude: 'Analyze /bin/ls for me'"
echo ""
echo "📚 Read the STUDENT_GUIDE.md for detailed learning materials"
echo ""
echo "Happy hacking! - Isaac Isalwa"
echo ""
