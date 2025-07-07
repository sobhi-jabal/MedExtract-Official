# MedExtract v1.0.0

## Overview

MedExtract is a software platform for extracting structured data from unstructured medical reports using large language models (LLMs). The system processes clinical text documents to identify and extract specific datapoints based on user-defined criteria.

## Primary Use Cases

- Extracting diagnoses, medications, and clinical findings from radiology reports
- Processing pathology reports for research data collection
- Analyzing clinical notes for quality improvement initiatives
- Structured data extraction for retrospective studies

## System Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Memory**: 16 GB RAM (32 GB recommended for large datasets)
- **Storage**: 50 GB available disk space
- **Software**: Docker Desktop (Windows/macOS) or Docker Engine (Linux)
- **Network**: Internet connection for initial setup

## Installation Files

### Windows
- `MedExtract-Windows-Installer.bat` - Automated installation script

### macOS/Linux  
- `MedExtract-Source-v1.0.0.tar.gz` - Complete source package with Unix installer
- `MedExtract-Source-v1.0.0.zip` - Alternative archive format

## Installation Instructions

### Windows Installation

1. Download `MedExtract-Windows-Installer.bat`
2. Right-click the file and select "Run as administrator"
3. Follow the on-screen prompts
4. Installation typically takes 15-20 minutes
5. Access the application at http://localhost:3000

### macOS/Linux Installation

1. Download `MedExtract-Source-v1.0.0.tar.gz`
2. Extract the archive: `tar -xzf MedExtract-Source-v1.0.0.tar.gz`
3. Navigate to the directory: `cd MedExtract-v1.0.0`
4. Run the installer: `./installer/install.sh`
5. Follow the prompts
6. Access the application at http://localhost:3000

## Key Features

- **Configurable Extraction**: Define custom datapoints with specific instructions
- **Batch Processing**: Process multiple reports simultaneously
- **Model Selection**: Choose from various LLM models based on accuracy/speed requirements
- **Export Options**: Results available in CSV and Excel formats
- **Validation Support**: Compare extractions against ground truth data when available
- **Progress Monitoring**: Real-time status updates during processing

## Technical Architecture

- **Backend**: FastAPI (Python) for data processing and LLM integration
- **Frontend**: Next.js web interface for configuration and monitoring
- **LLM Integration**: Ollama for local model deployment
- **Containerization**: Docker for consistent deployment across systems

## Data Privacy

All processing occurs locally on your machine. No data is transmitted to external servers. Models run in isolated containers for security.

## Documentation

Comprehensive guides are included in the `docs/` directory:
- `INSTALLATION.md` - Detailed setup instructions
- `USER_GUIDE.md` - Step-by-step usage instructions

## Support

For technical issues or questions:
- Review the documentation in the `docs/` directory
- Submit issues via GitHub's issue tracker
- Contact the development team

## Citation

If you use MedExtract in your research, please cite:
```
MedExtract: Automated Medical Report Data Extraction Platform (v1.0.0)
https://github.com/sobhi-jabal/MedExtract-Official
```

## License

MIT License - see LICENSE file for complete terms