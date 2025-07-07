# MedExtract

## Overview

MedExtract extracts structured data from unstructured medical reports using large language models. All processing occurs locally within your institution.

## Clinical Applications

- Clinical research: retrospective cohort identification, data collection
- Quality assurance: documentation review for compliance
- Registry population: automated data extraction
- Outcomes research: structured data from narrative reports

Supports radiology reports, pathology reports, clinical notes, operative reports, and consultation reports.

## Requirements

- Operating System: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+, RHEL 8+)
- Memory: 16 GB RAM minimum (32 GB recommended)
- Storage: 50 GB available
- Processor: x86_64, 4+ cores
- Docker Desktop 4.0+ or Docker Engine 20.10+

Processing speed: 100-500 reports/hour depending on hardware.

## Installation

### Windows
1. Download installer from [Releases](https://github.com/sobhi-jabal/MedExtract-Official/releases)
2. Run as administrator
3. Follow prompts
4. Access at http://localhost:3000

### macOS/Linux
1. Download archive from [Releases](https://github.com/sobhi-jabal/MedExtract-Official/releases)
2. Extract: `tar -xzf MedExtract-*.tar.gz`
3. Install: `cd MedExtract-* && sudo ./installer/install.sh`
4. Access at http://localhost:3000

## Documentation

- [Installation Guide](docs/INSTALLATION_GUIDE.md)
- [Clinical User Guide](docs/CLINICAL_USER_GUIDE.md)
- [System Requirements](docs/SYSTEM_REQUIREMENTS.md)
- [Data Privacy & Security](docs/DATA_PRIVACY_SECURITY.md)
- API Documentation: http://localhost:8000/docs (after installation)

## Features

- Configure custom data extraction fields
- Batch processing of multiple documents
- Validation against ground truth data
- Export to CSV or Excel formats
- Multiple model options for different use cases
- Configurable parameters for optimization

## Privacy and Security

- All processing occurs locally
- No external data transmission
- Containerized architecture for isolation
- Audit logging for compliance
- Functions in air-gapped environments
- HIPAA-compliant deployment options

## Citation

```bibtex
@software{medextract2024,
  title = {MedExtract: Automated Data Extraction from Clinical Reports},
  version = {1.0.0},
  year = {2024},
  url = {https://github.com/sobhi-jabal/MedExtract-Official}
}
```

## Support

- Issues: [GitHub Issues](https://github.com/sobhi-jabal/MedExtract-Official/issues)
- Documentation: See `docs/` directory
- Version support: 24 months

### Limitations
- English language only
- Text extraction only
- Single-node deployment
- Requires validation for clinical use

## License

MIT License - See LICENSE file for complete terms.

---

Version 1.0.0