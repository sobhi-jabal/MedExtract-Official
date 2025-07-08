# MedExtract Version 1.0.0

## Overview

MedExtract extracts structured data from unstructured medical reports using large language models. The system processes clinical documentation locally, converting narrative text into analyzable data formats.

## Clinical Applications

### Use Cases
- Radiology report analysis: findings, impressions, recommendations
- Pathology data extraction: diagnostic findings, staging information
- Clinical research: retrospective chart review, cohort identification
- Quality assurance: documentation completeness, clinical indicators
- Registry population: automated data collection

### Supported Report Types
- Radiology reports (all modalities)
- Pathology reports
- Clinical notes
- Operative reports
- Consultation reports

## Architecture

### Components
- Containerized deployment using Docker
- Web interface for configuration and monitoring
- FastAPI backend for data processing
- Ollama for local model inference
- Batch processing with parallelization

### Security
- Local processing only
- No external data transmission
- Authentication support
- Audit logging
- HIPAA-compliant deployment options

## System Requirements

### Minimum Requirements
- Processor: x86_64, 4 cores
- Memory: 16 GB RAM
- Storage: 50 GB available
- Network: Internet for initial setup only

### Recommended Requirements
- Processor: 8+ cores
- Memory: 32 GB RAM
- Storage: 100 GB SSD
- GPU: NVIDIA with 8GB+ VRAM (optional)

### Software Requirements
- Operating Systems: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+, RHEL 8+)
- Docker Desktop 4.0+ or Docker Engine 20.10+
- Modern web browser

## Download

### Installation Files
- `MEDEXTRACT-INSTALL.bat` - Windows batch installer (8.7 KB)
  - SHA256: `48a123988dca98290624598496dad9c1099be0c772f377556ec6ddf30c9fe2e8`
- `install.sh` - Unix/Linux/macOS installer script (8.2 KB)
  - SHA256: `1f74c256c108f19c510fff6ea553dde2aa39873f59e8ab685416ad9f53cccf42`

### Source Code Archives
- `medextract-v1.0.0.tar.gz` - Complete source code (295 KB)
  - SHA256: `8802572b7eeb96a2dec6a382ebd369d1bae79c5bfdb1f0a981a0c836c41e4c3e`
- `medextract-v1.0.0.zip` - Complete source code (158 KB)
  - SHA256: `c6deb8b68c3a800260c5497ec3bdf2a459e9532fc0a7352f1e1ba3f6747b7ddf`

## Installation

### Windows
1. Verify system requirements
2. Install Docker Desktop
3. Download and run `MEDEXTRACT-INSTALL.bat` as administrator
4. Follow the installation prompts
5. Access application at http://localhost:3000

### macOS/Linux
1. Verify system requirements  
2. Install Docker
3. Download and extract source archive (`medextract-v1.0.0.tar.gz`)
4. Run `./install.sh` with sudo privileges
5. Access application at http://localhost:3000

Detailed instructions available in `docs/INSTALLATION_GUIDE.md`

## Available Models

- `phi4:latest` - Medical terminology optimization
- `llama2:13b` - General medical text processing
- `mistral:7b` - Fast processing for simple extractions

Model selection depends on accuracy requirements, processing speed needs, and available hardware.

## Data Specifications

### Input
- File formats: CSV, XLSX, XLS
- Text encoding: UTF-8
- Maximum file size: 500 MB
- Maximum batch size: 10,000 reports

### Output
- CSV with extracted fields
- Excel format available
- Includes confidence scores and timestamps

## Performance

### Processing Speed
- Single report: 2-5 seconds (CPU), 0.5-2 seconds (GPU)
- Batch processing: 100-500 reports/hour
- Memory usage: 4-8 GB baseline plus model requirements

### Accuracy
- Typical accuracy: 85-95% depending on report complexity
- Validation against ground truth supported
- Metrics: precision, recall, F1 scores

## Limitations

- Single-node deployment
- English language models only
- Text extraction only (no image analysis)
- Not for real-time clinical decisions
- Requires human validation
- No direct EMR integration

## Documentation

- Installation: `docs/INSTALLATION_GUIDE.md`
- User Guide: `docs/CLINICAL_USER_GUIDE.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
- API Reference: `http://localhost:8000/docs`

Version 1.0.0 supported for 24 months with quarterly security updates.

## Compliance

- Research tool only
- Not FDA-approved for clinical diagnosis
- Validation required for clinical use
- Audit logging included
- All processing remains local
- No cloud dependencies

## Citation

```
MedExtract: Automated Data Extraction from Clinical Reports
Version 1.0.0
https://github.com/sobhi-jabal/MedExtract-Official
```

## License

This software is distributed under the MIT License. See LICENSE file for complete terms.

---

Release Date: January 2024
Version: 1.0.0