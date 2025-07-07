#!/bin/bash

# MedExtract Installer for macOS and Linux
# Simplified version focused on reliability and ease of use

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
INSTALL_DIR="$HOME/MedExtract"

# Banner
echo -e "${CYAN}"
cat << "EOF"

  __  __          _ _____      _                  _   
 |  \/  |        | |  ___|    | |                | |  
 | \  / | ___  __| | |__  __ _| |_ _ __ __ _  ___| |_ 
 | |\/| |/ _ \/ _` |  __| \ \/ / __| '__/ _` |/ __| __|
 | |  | |  __/ (_| | |____ >  <| |_| | | (_| | (__| |_ 
 |_|  |_|\___|\__,_\____/_/_/\_\\__|_|  \__,_|\___|\__|
                                                        
        Medical Report Data Extraction Platform
        Version 1.0.0
  
EOF
echo -e "${NC}"

echo -e "${GREEN}MedExtract Installer for $(uname)${NC}"
echo -e "${GREEN}======================================${NC}\n"

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo -e "${RED}ERROR: Unsupported operating system${NC}"
    exit 1
fi

echo -e "Detected OS: ${BLUE}$OS${NC}"

# Check if running from extracted directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}ERROR: Installation files not found${NC}"
    echo "Please run this script from the extracted MedExtract directory"
    exit 1
fi

# Function to check command
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check Docker
echo -e "\n[1/5] Checking Docker..."

if ! command_exists docker; then
    echo -e "${RED}ERROR: Docker not installed${NC}\n"
    
    if [[ "$OS" == "macos" ]]; then
        echo "Please install Docker Desktop from:"
        echo "  https://www.docker.com/products/docker-desktop"
    else
        echo "Please install Docker from:"
        echo "  https://docs.docker.com/engine/install/"
    fi
    echo -e "\nAfter installation, run this installer again."
    exit 1
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${YELLOW}Docker is installed but not running${NC}"
    
    if [[ "$OS" == "macos" ]]; then
        echo "Starting Docker Desktop..."
        open -a Docker 2>/dev/null || {
            echo -e "${RED}Failed to start Docker Desktop${NC}"
            echo "Please start Docker Desktop manually"
            exit 1
        }
        
        echo "Waiting for Docker to start (up to 60 seconds)..."
        COUNTER=0
        while [ $COUNTER -lt 60 ]; do
            if docker info >/dev/null 2>&1; then
                break
            fi
            sleep 2
            COUNTER=$((COUNTER + 2))
            echo -n "."
        done
        echo
        
        if [ $COUNTER -ge 60 ]; then
            echo -e "${RED}Docker failed to start${NC}"
            echo "Please start Docker Desktop manually and try again"
            exit 1
        fi
    else
        echo "Please start Docker:"
        echo "  sudo systemctl start docker"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Docker is running${NC}"

# Check Docker Compose
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command_exists docker-compose; then
    COMPOSE_CMD="docker-compose"
else
    echo -e "${RED}ERROR: Docker Compose not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker Compose available${NC}"

# Step 2: Setup installation directory
echo -e "\n[2/5] Setting up installation..."

# If install directory exists, ask user
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}MedExtract directory already exists at: $INSTALL_DIR${NC}"
    read -p "Remove existing installation? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping existing services..."
        if [ -f "$INSTALL_DIR/stop-medextract.sh" ]; then
            "$INSTALL_DIR/stop-medextract.sh" >/dev/null 2>&1 || true
        fi
        rm -rf "$INSTALL_DIR"
    else
        echo "Installation cancelled"
        exit 0
    fi
fi

# Create install directory and copy files
echo "Copying files to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR/"

echo -e "${GREEN}✓ Files copied${NC}"

# Step 3: Check ports
echo -e "\n[3/5] Checking ports..."

check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1
    fi
    return 0
}

FRONTEND_PORT=3000
BACKEND_PORT=8000

if ! check_port $FRONTEND_PORT; then
    echo -e "${RED}ERROR: Port $FRONTEND_PORT is already in use${NC}"
    echo "Please stop the service using this port and try again"
    exit 1
fi

if ! check_port $BACKEND_PORT; then
    echo -e "${RED}ERROR: Port $BACKEND_PORT is already in use${NC}"
    echo "Please stop the service using this port and try again"
    exit 1
fi

echo -e "${GREEN}✓ Ports available${NC}"

# Step 4: Create scripts
echo -e "\n[4/5] Creating management scripts..."

# Start script
cat > "$INSTALL_DIR/start-medextract.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "Starting MedExtract..."

# Check for local Ollama
if command -v ollama >/dev/null 2>&1 && curl -s http://localhost:11434 >/dev/null 2>&1; then
    echo "Using local Ollama installation"
    export USE_LOCAL_OLLAMA=true
    if [ -f "docker-compose.duke.yml" ]; then
        docker compose -f docker-compose.duke.yml up -d
    else
        docker compose up -d
    fi
else
    echo "Using containerized Ollama"
    docker compose up -d
fi

echo ""
echo "MedExtract is starting..."
echo "Access the application at: http://localhost:3000"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop: ./stop-medextract.sh"
EOF

chmod +x "$INSTALL_DIR/start-medextract.sh"

# Stop script
cat > "$INSTALL_DIR/stop-medextract.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "Stopping MedExtract..."

if [ -f "docker-compose.duke.yml" ] && [ "$USE_LOCAL_OLLAMA" = "true" ]; then
    docker compose -f docker-compose.duke.yml down
else
    docker compose down
fi

echo "MedExtract stopped."
EOF

chmod +x "$INSTALL_DIR/stop-medextract.sh"

# Uninstall script
cat > "$INSTALL_DIR/uninstall-medextract.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "Uninstalling MedExtract..."

# Stop services
./stop-medextract.sh

# Remove Docker images
docker rmi medextract-backend:latest medextract-frontend:latest >/dev/null 2>&1 || true

# Remove installation directory
cd ..
rm -rf MedExtract

echo "MedExtract has been uninstalled."
EOF

chmod +x "$INSTALL_DIR/uninstall-medextract.sh"

echo -e "${GREEN}✓ Scripts created${NC}"

# Step 5: Build and start
echo -e "\n[5/5] Building MedExtract (this may take 10-20 minutes)..."

cd "$INSTALL_DIR"

# Check for local Ollama
if command_exists ollama && curl -s http://localhost:11434 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Local Ollama detected - no model downloads needed${NC}"
    export USE_LOCAL_OLLAMA=true
    if [ -f "docker-compose.duke.yml" ]; then
        COMPOSE_FILE="docker-compose.duke.yml"
    else
        COMPOSE_FILE="docker-compose.yml"
    fi
else
    COMPOSE_FILE="docker-compose.yml"
fi

# Build containers
echo "Building Docker containers..."
$COMPOSE_CMD -f "$COMPOSE_FILE" build --no-cache

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Build failed${NC}"
    echo "Check Docker logs for details"
    exit 1
fi

echo -e "${GREEN}✓ Build complete${NC}"

# Start services
echo -e "\nStarting services..."
$COMPOSE_CMD -f "$COMPOSE_FILE" up -d

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to start services${NC}"
    exit 1
fi

# Success message
echo -e "\n${GREEN}============================================"
echo -e "✓ MedExtract Installation Complete!"
echo -e "============================================${NC}\n"

echo "Installation location: $INSTALL_DIR"
echo ""
echo "MedExtract is now running at:"
echo -e "  ${BLUE}http://localhost:3000${NC}"
echo ""
echo "Commands:"
echo "  Start:     $INSTALL_DIR/start-medextract.sh"
echo "  Stop:      $INSTALL_DIR/stop-medextract.sh"
echo "  Uninstall: $INSTALL_DIR/uninstall-medextract.sh"
echo ""

# Try to open browser
if [[ "$OS" == "macos" ]]; then
    echo "Opening browser..."
    open "http://localhost:3000" 2>/dev/null || true
elif command_exists xdg-open; then
    xdg-open "http://localhost:3000" 2>/dev/null || true
fi

echo -e "${GREEN}Installation complete!${NC}"