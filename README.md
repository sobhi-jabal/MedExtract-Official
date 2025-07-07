# MedExtract - Medical Report Data Extraction Platform

MedExtract is a powerful, AI-driven platform for extracting structured data from unstructured medical reports. Built with modern technologies and designed for institutional use, it provides a user-friendly interface for healthcare professionals and researchers.

## Features

- **AI-Powered Extraction**: Utilizes state-of-the-art language models for accurate data extraction
- **Flexible Configuration**: Customize extraction parameters and datapoints
- **Batch Processing**: Process multiple reports simultaneously
- **Real-time Progress**: Monitor extraction progress with live updates
- **Multiple Export Formats**: Export results as CSV or Excel files
- **RAG Support**: Optional Retrieval-Augmented Generation for improved accuracy
- **Corporate Network Ready**: Works behind firewalls and with proxy settings

## System Requirements

- Windows 10/11 (64-bit)
- 16GB RAM minimum (32GB recommended)
- 50GB free disk space
- Administrator privileges for installation
- Docker Desktop installed and running

## Quick Start

### Windows Installation

1. **Download the installer**
   - Download `MEDEXTRACT-INSTALL.bat` from the [Releases](https://github.com/sobhi-jabal/MedExtract-Official/releases) page

2. **Run as Administrator**
   - Right-click `MEDEXTRACT-INSTALL.bat`
   - Select "Run as administrator"

3. **Follow the installer**
   - The installer will automatically:
     - Check system requirements
     - Install MedExtract
     - Configure for your environment
     - Create desktop shortcuts

4. **Access the application**
   - Open browser to http://localhost:3000
   - Or use the desktop shortcut

### macOS/Linux Installation

1. **Download and extract**
   - Download the source archive from the [Releases](https://github.com/sobhi-jabal/MedExtract-Official/releases) page
   - Extract to your desired location

2. **Run the installer**
   ```bash
   cd medextract
   ./installer/install.sh
   ```

3. **Follow the prompts**
   - The installer will check for Docker
   - Build and configure MedExtract
   - Create management scripts

4. **Access the application**
   - Open browser to http://localhost:3000
   - Use the created scripts to start/stop

### Manual Installation

For advanced users:

```bash
# Extract the archive
tar -xzf medextract-v1.0.0.tar.gz
cd medextract

# Build and start services
docker-compose build
docker-compose up -d

# Access at http://localhost:3000
```

## Usage

1. **Upload Data**
   - Click "Create New Job"
   - Upload CSV or Excel file containing medical reports
   - Select the column containing report text

2. **Configure Extraction**
   - Define datapoints to extract
   - Set extraction parameters
   - Choose LLM model

3. **Run Extraction**
   - Click "Start Extraction"
   - Monitor real-time progress
   - Download results when complete

## Architecture

MedExtract consists of three main components:

- **Frontend**: Next.js-based web interface
- **Backend**: FastAPI server handling extraction logic
- **LLM Service**: Ollama for running language models

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# API Configuration
API_URL=http://localhost:8000

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434

# Corporate Network (optional)
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
```

### Docker Compose Variants

- `docker-compose.yml`: Default configuration
- `docker-compose.duke.yml`: Configuration for Duke Health systems
- `docker-compose.real.yml`: Production configuration with Ollama

## Troubleshooting

### Docker Not Found
- Ensure Docker Desktop is installed
- Add Docker to system PATH
- Restart after installation

### Model Download Issues
- Check internet connectivity
- For corporate networks, use local Ollama
- Configure proxy settings if needed

### Port Conflicts
- Default ports: 3000 (frontend), 8000 (backend)
- Modify docker-compose.yml if conflicts exist

## Support

For issues and questions:
- Create an issue on GitHub
- Contact the development team
- Review documentation in `/docs`

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Acknowledgments

Developed by the MedExtract team for healthcare data extraction research.