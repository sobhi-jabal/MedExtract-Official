# MedExtract v1.0.0

Extracts structured datapoints from unstructured medical reports using large language models. Designed for retrospective research, registry population, and quality metrics extraction from radiology reports, pathology findings, and clinical notes.

## Key Features

- **Structured data extraction** - Convert free-text reports into analyzable datapoints
- **Configurable pipeline** - Customize extraction workflow, processing steps, and output formats
- **Custom prompt engineering** - Define specific extraction instructions for each datapoint
- **RAG with medical reranker** - BGE-reranker-v2-m3 optimizes relevant context retrieval
- **Few-shot learning** - Provide examples to guide extraction patterns
- **Batch processing** - Process thousands of reports with progress tracking
- **Ground truth validation** - Validate extractions against known data
- **Multiple model support** - Choose between phi4, llama2, mistral based on needs

## Privacy & Architecture

- Fully local processing - no external API calls
- Docker containerization for secure deployment
- All data remains within your institution
- No cloud dependencies

## System Requirements

| Component | Requirement |
|-----------|-------------|
| Memory | 16 GB RAM (32 GB recommended) |
| Storage | 50 GB available |
| Software | Docker Desktop |
| OS | Windows 10/11, macOS 10.15+, Linux |

## Downloads

- `MEDEXTRACT-INSTALL.bat` - Windows installer (8.7 KB)
- `install.sh` - macOS/Linux installer (8.2 KB)
- `medextract-v1.0.0.tar.gz` - Source code (295 KB)

## Installation

### Windows
1. Install Docker Desktop
2. Run MEDEXTRACT-INSTALL.bat as administrator
3. Access at http://localhost:3000

### macOS/Linux
1. Install Docker
2. Extract source and run ./install.sh
3. Access at http://localhost:3000

Full guide: `docs/INSTALLATION_GUIDE.md`

## Documentation

- Installation Guide: `docs/INSTALLATION_GUIDE.md`
- User Guide: `docs/CLINICAL_USER_GUIDE.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`

## Citation

```
MedExtract: Automated Data Extraction from Clinical Reports
Version 1.0.0
https://github.com/sobhi-jabal/MedExtract-Official
```

---

MIT License | January 2024