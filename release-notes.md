# MedExtract v1.0.0 - Initial Release

## Overview
MedExtract is an AI-powered platform for extracting structured data from unstructured medical reports. Built with modern technologies and designed for institutional use.

## Core Features
- **AI-powered medical data extraction** from unstructured text
- **Advanced language model integration** with customizable parameters
- **Real-time extraction monitoring** and progress tracking
- **Batch processing** with checkpoint recovery
- **RAG support** for complex extractions
- **RESTful API** with comprehensive documentation
- **Modern web interface** built with Next.js
- **Docker-based deployment** for consistency

## Installation

### Quick Install - Windows
1. Download `MEDEXTRACT-INSTALL.bat`
2. Right-click and select "Run as administrator"
3. Follow the installation prompts

### Quick Install - macOS/Linux
1. Download and extract the source archive
2. Run `./installer/install.sh`
3. Follow the installation prompts

### Manual Installation
```bash
git clone https://github.com/sobhi-jabal/MedExtract-Official.git
cd MedExtract-Official
docker-compose build
docker-compose up -d
```

## Requirements
- **OS**: Windows 10/11, macOS, or Linux
- **Docker**: Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- **RAM**: 16GB minimum (32GB recommended)
- **Storage**: 50GB free disk space

## Documentation
- [Installation Guide](docs/INSTALLATION.md)
- [User Guide](docs/USER_GUIDE.md)
- [Contributing](CONTRIBUTING.md)

## Technical Stack
- **Backend**: FastAPI with async processing
- **Frontend**: Next.js with TypeScript
- **LLM**: Ollama integration
- **Deployment**: Docker Compose

## Downloads
- **Windows**: Use `MEDEXTRACT-INSTALL.bat`
- **macOS/Linux**: Use `install.sh` from source archive
- **Source Code**: Available in ZIP and TAR.GZ formats

## License
MIT License - see LICENSE file for details.