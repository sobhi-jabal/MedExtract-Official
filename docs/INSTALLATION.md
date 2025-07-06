# MedExtract Installation Guide

## Table of Contents
- [System Requirements](#system-requirements)
- [Windows Installation](#windows-installation)
- [Corporate Network Setup](#corporate-network-setup)
- [Manual Installation](#manual-installation)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11 (64-bit)
- **RAM**: 16GB
- **Storage**: 50GB free space
- **CPU**: 4 cores
- **Network**: Internet connection for initial setup

### Recommended Requirements
- **RAM**: 32GB or more
- **Storage**: 100GB free space
- **CPU**: 8 cores or more
- **GPU**: NVIDIA GPU with 8GB+ VRAM (for faster processing)

### Software Prerequisites
- Docker Desktop (latest version)
- Administrator privileges

## Windows Installation

### Automated Installation (Recommended)

1. **Download the Installer**
   - Download `MEDEXTRACT-INSTALL.bat` from the releases page
   - Save to a location you can easily access

2. **Prepare System**
   - Close all unnecessary applications
   - Ensure you have administrator access
   - Temporarily disable antivirus if it blocks scripts

3. **Run the Installer**
   ```
   1. Right-click MEDEXTRACT-INSTALL.bat
   2. Select "Run as administrator"
   3. Follow the on-screen instructions
   ```

4. **Installation Process**
   The installer will:
   - Check for administrator privileges
   - Verify Docker Desktop installation
   - Clean any previous installations
   - Download MedExtract components
   - Build Docker containers (10-20 minutes)
   - Create desktop shortcuts
   - Start the application

5. **Post-Installation**
   - Desktop shortcuts created:
     - `MedExtract.bat` - Start the application
     - `Stop-MedExtract.bat` - Stop the application
   - Application available at: http://localhost:3000

## Corporate Network Setup

### For Duke Health and Similar Networks

1. **Network Detection**
   - The installer automatically detects corporate networks
   - Configures proxy settings if needed
   - Uses local Ollama if available

2. **TLS Certificate Issues**
   If you encounter TLS certificate errors:
   ```
   - Install Ollama locally on your machine
   - The installer will detect and use it automatically
   - No model downloads through corporate proxy needed
   ```

3. **Proxy Configuration**
   For manual proxy setup, create `.env` file:
   ```env
   HTTP_PROXY=http://your-proxy:8080
   HTTPS_PROXY=http://your-proxy:8080
   NO_PROXY=localhost,127.0.0.1
   ```

## Manual Installation

### Using Docker Compose

1. **Clone Repository**
   ```bash
   git clone https://github.com/your-org/medextract.git
   cd medextract
   ```

2. **Configure Environment**
   ```bash
   # Copy example environment
   cp .env.example .env
   
   # Edit .env with your settings
   ```

3. **Choose Configuration**
   ```bash
   # For standard setup
   cp docker-compose.real.yml docker-compose.yml
   
   # For Duke Health systems
   cp docker-compose.duke.yml docker-compose.yml
   ```

4. **Build and Start**
   ```bash
   # Build containers
   docker-compose build --no-cache
   
   # Start services
   docker-compose up -d
   ```

5. **Verify Installation**
   ```bash
   # Check services
   docker-compose ps
   
   # View logs
   docker-compose logs -f
   ```

## Verification

### Check Installation

1. **Service Status**
   ```bash
   docker ps
   ```
   Should show:
   - medextract-backend
   - medextract-frontend
   - ollama (if using containerized)

2. **Access Points**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

3. **Test Extraction**
   - Upload a sample CSV file
   - Create a simple extraction job
   - Verify results download

## Troubleshooting

### Common Issues

#### Docker Desktop Not Found
```
Error: Docker Desktop not installed
```
**Solution**:
1. Download Docker Desktop from https://docker.com
2. Install and restart computer
3. Run installer again

#### Docker Not Starting
```
Error: Docker daemon not running
```
**Solution**:
1. Start Docker Desktop manually
2. Wait for it to fully initialize
3. Run installer again

#### Port Already in Use
```
Error: Port 3000 or 8000 already in use
```
**Solution**:
1. Stop conflicting services
2. Or modify ports in docker-compose.yml

#### Build Failures
```
Error: Build failed
```
**Solution**:
1. Check disk space (need 50GB+)
2. Check internet connection
3. Run with --no-cache flag
4. Check Docker Desktop resources

#### Model Download Issues
```
Error: TLS certificate verification failed
```
**Solution**:
1. Install Ollama locally
2. Use docker-compose.duke.yml
3. Configure proxy settings

### Getting Help

1. **Check Logs**
   ```bash
   # Installation log
   type %TEMP%\medextract-install.log
   
   # Docker logs
   docker-compose logs backend
   docker-compose logs frontend
   ```

2. **System Information**
   Include when reporting issues:
   - Windows version
   - Docker Desktop version
   - Network type (corporate/home)
   - Error messages
   - Log files

3. **Support Channels**
   - GitHub Issues
   - Email support
   - Documentation wiki

## Next Steps

After successful installation:
1. Read the [User Guide](USER_GUIDE.md)
2. Try the [Quick Start Tutorial](QUICK_START.md)
3. Configure [Advanced Settings](CONFIGURATION.md)
4. Set up [Model Management](MODELS.md)