# MedExtract System Requirements

## Executive Summary

This document provides comprehensive technical specifications for deploying MedExtract in healthcare environments. Requirements are categorized by deployment scale and use case to assist IT departments in planning appropriate infrastructure.

## Hardware Requirements

### Minimum Configuration

Suitable for small-scale deployments (< 1,000 reports/day):

| Component | Specification | Rationale |
|-----------|--------------|-----------|
| **CPU** | x86_64 architecture, 4 cores @ 2.4GHz | Required for concurrent processing |
| **RAM** | 16 GB DDR4 | Base system (8GB) + Model loading (8GB) |
| **Storage** | 50 GB SSD | OS (20GB) + Docker images (20GB) + Working space (10GB) |
| **Network** | 1 Gbps Ethernet | Local processing only; internet for setup |

### Recommended Configuration

Suitable for department-level deployments (1,000-10,000 reports/day):

| Component | Specification | Rationale |
|-----------|--------------|-----------|
| **CPU** | x86_64 architecture, 8 cores @ 3.0GHz | Improved parallelization |
| **RAM** | 32 GB DDR4 | Larger model support + caching |
| **Storage** | 250 GB NVMe SSD | Faster I/O for batch processing |
| **GPU** | NVIDIA RTX 3060 (12GB VRAM) | 3-5x processing acceleration |
| **Network** | 1 Gbps Ethernet | Sufficient for all operations |

### Enterprise Configuration

Suitable for institution-wide deployments (> 10,000 reports/day):

| Component | Specification | Rationale |
|-----------|--------------|-----------|
| **CPU** | AMD EPYC/Intel Xeon, 16+ cores | Maximum throughput |
| **RAM** | 64-128 GB ECC | Large batch processing |
| **Storage** | 1 TB NVMe SSD RAID 1 | Redundancy + performance |
| **GPU** | NVIDIA A40/A100 (24-48GB VRAM) | Production-grade acceleration |
| **Network** | 10 Gbps Ethernet | High-volume data transfer |

## Software Requirements

### Operating Systems

#### Windows
- **Versions**: Windows 10 Professional/Enterprise (Version 21H2+), Windows 11 Professional/Enterprise
- **Architecture**: 64-bit only
- **Features Required**: 
  - Hyper-V enabled
  - Windows Subsystem for Linux 2 (WSL2)
  - Virtualization enabled in BIOS

#### macOS
- **Versions**: macOS 10.15 (Catalina) or later
- **Hardware**: Intel or Apple Silicon (M1/M2/M3)
- **Features Required**:
  - Rosetta 2 (for Apple Silicon)
  - Full disk access permissions

#### Linux
- **Distributions**:
  - Ubuntu 20.04 LTS, 22.04 LTS
  - Red Hat Enterprise Linux 8.x, 9.x
  - CentOS Stream 8, 9
  - SUSE Linux Enterprise Server 15 SP3+
- **Kernel**: 5.4 or later
- **Features Required**:
  - systemd
  - cgroups v2 support

### Container Platform

#### Docker Requirements
- **Docker Desktop** (Windows/macOS):
  - Version 4.0.0 or later
  - Configured resources: 8GB RAM minimum
  - Storage driver: overlay2
  
- **Docker Engine** (Linux):
  - Version 20.10.0 or later
  - Docker Compose v2.0.0 or later
  - Storage driver: overlay2 or btrfs

#### Container Resource Allocation
```yaml
Minimum Allocation:
  CPUs: 4
  Memory: 8 GB
  Swap: 2 GB
  Disk: 20 GB

Recommended Allocation:
  CPUs: 8
  Memory: 16 GB
  Swap: 4 GB
  Disk: 50 GB
```

### Browser Requirements

For accessing the web interface:

| Browser | Minimum Version | Recommended Version |
|---------|----------------|-------------------|
| Google Chrome | 90 | Latest stable |
| Mozilla Firefox | 88 | Latest stable |
| Microsoft Edge | 90 | Latest stable |
| Safari | 14 | Latest stable |

JavaScript must be enabled, and WebSocket support is required.

## Network Requirements

### Connectivity

#### Installation Phase
- **Internet Access**: Required for initial setup
- **Bandwidth**: Minimum 10 Mbps for model downloads
- **Protocols**: HTTPS (443), HTTP (80)
- **Duration**: 30-60 minutes for full installation

#### Operational Phase
- **Internet Access**: Not required (air-gapped operation supported)
- **Internal Network**: Required for multi-user access
- **Protocols**: HTTP/HTTPS for web interface
- **Firewall Rules**: Allow internal access to ports 3000, 8000

### Port Configuration

| Service | Default Port | Protocol | Purpose |
|---------|-------------|----------|---------|
| Frontend | 3000 | HTTP | Web interface |
| Backend API | 8000 | HTTP | REST API |
| Ollama Service | 11434 | HTTP | Model inference |
| PostgreSQL* | 5432 | TCP | Database (if configured) |

*Optional component for persistent storage

### Proxy Configuration

For environments with HTTP proxy:

```bash
Environment Variables:
HTTP_PROXY=http://proxy.institution.edu:8080
HTTPS_PROXY=http://proxy.institution.edu:8080
NO_PROXY=localhost,127.0.0.1,*.local
```

## Storage Requirements

### Disk Space Allocation

| Component | Initial | 6 Months | 12 Months | Notes |
|-----------|---------|----------|-----------|--------|
| **System** | 5 GB | 5 GB | 5 GB | OS integration |
| **Docker Images** | 15 GB | 15 GB | 15 GB | Base images |
| **Language Models** | 20 GB | 30 GB | 40 GB | Additional models |
| **Application Data** | 5 GB | 50 GB | 100 GB | Logs, temporary files |
| **User Data** | Variable | Variable | Variable | Based on usage |
| **Total** | 45 GB | 100 GB | 155 GB | Minimum estimates |

### Storage Performance

| Metric | Minimum | Recommended | Impact |
|--------|---------|-------------|--------|
| **Sequential Read** | 200 MB/s | 500 MB/s | Model loading |
| **Sequential Write** | 100 MB/s | 300 MB/s | Result export |
| **Random IOPS** | 1,000 | 10,000 | Database operations |
| **Latency** | < 10ms | < 1ms | UI responsiveness |

### Backup Requirements

- **Backup Frequency**: Daily incremental, weekly full
- **Retention Period**: 30 days minimum
- **Backup Storage**: 2x operational storage
- **Recovery Time Objective**: < 4 hours

## Performance Specifications

### Processing Capacity

| Configuration | Reports/Hour | Concurrent Users | Response Time |
|--------------|--------------|------------------|---------------|
| **Minimum** | 100-200 | 1-5 | 2-5 sec/report |
| **Recommended** | 300-500 | 5-20 | 1-2 sec/report |
| **Enterprise** | 1000+ | 20-50 | <1 sec/report |

### Memory Utilization

| Component | Base | Per User | Per 1000 Reports |
|-----------|------|----------|------------------|
| **Frontend** | 500 MB | 50 MB | N/A |
| **Backend** | 2 GB | 100 MB | 500 MB |
| **Ollama** | 4 GB | N/A | 1 GB |
| **Database** | 1 GB | 10 MB | 100 MB |

### GPU Acceleration

When available, GPU acceleration provides:
- 3-5x faster inference
- Reduced CPU utilization
- Support for larger models
- Concurrent batch processing

## Scalability Considerations

### Vertical Scaling

Increasing single-server capacity:
1. Add RAM for larger batch sizes
2. Add CPU cores for parallelization
3. Add GPU for acceleration
4. Upgrade storage for I/O performance

### Horizontal Scaling

Future architecture supports:
- Load balancer integration
- Distributed processing
- Shared storage backends
- Container orchestration

### Performance Tuning

Key parameters for optimization:
```yaml
Batch Processing:
  batch_size: 10-50 (based on RAM)
  worker_threads: CPU_cores - 2
  model_cache: true
  
Model Configuration:
  context_window: 2048
  gpu_layers: 35 (if GPU available)
  thread_count: CPU_cores
```

## Monitoring Requirements

### System Metrics

Essential monitoring points:
- CPU utilization (target: <80%)
- Memory usage (target: <85%)
- Disk I/O (queue depth <10)
- Network throughput
- Container health status

### Application Metrics

- Processing queue length
- Average processing time
- Error rates
- Model inference latency
- API response times

### Logging Requirements

- **Log Retention**: 90 days
- **Log Storage**: 10 GB minimum
- **Log Levels**: INFO default, DEBUG available
- **Log Format**: JSON structured logging

## Security Requirements

### System Hardening

- Disable unnecessary services
- Apply latest OS patches
- Configure local firewall
- Enable audit logging
- Implement access controls

### Container Security

- Use official base images only
- Regular security scanning
- Non-root container execution
- Read-only root filesystem
- Network segmentation

### Data Protection

- Encrypted storage (at rest)
- TLS for network communication
- Secure credential management
- Regular security updates
- Access audit trails

## Compliance Considerations

### HIPAA Requirements

For HIPAA-covered entities:
- Encryption at rest and in transit
- Access controls and audit logs
- Automatic logoff (configurable)
- Backup and disaster recovery
- Business Associate Agreement (if applicable)

### Validation Requirements

- IQ/OQ/PQ documentation available
- Change control procedures
- System validation protocols
- Performance qualification testing
- Ongoing monitoring procedures

## Virtualization Support

### Supported Platforms

| Platform | Version | Notes |
|----------|---------|--------|
| VMware vSphere | 7.0+ | Full support |
| Microsoft Hyper-V | 2019+ | Full support |
| KVM/QEMU | RHEL 8+ | Full support |
| Proxmox VE | 7.0+ | Community tested |

### Virtual Machine Configuration

```yaml
Minimum VM Specifications:
  vCPUs: 4
  Memory: 16 GB (reserved)
  Storage: 50 GB (thick provisioned)
  Network: VMXNET3 or VirtIO
  
GPU Passthrough:
  Supported with appropriate hypervisor configuration
  Requires IOMMU/VT-d enabled
```

## Cloud Deployment

### Private Cloud

Supported platforms:
- OpenStack (Rocky+)
- VMware vCloud
- OpenShift Container Platform
- Kubernetes (1.21+)

### Public Cloud (Development Only)

Not recommended for production PHI:
- AWS EC2 (m5.xlarge minimum)
- Azure VM (Standard_D4s_v3 minimum)
- Google Compute Engine (n2-standard-4 minimum)

## Support Matrix

### End of Support Dates

| Component | Version | End of Support |
|-----------|---------|----------------|
| Windows 10 21H2 | 21H2 | June 2024 |
| Ubuntu 20.04 | 20.04 | April 2025 |
| Docker 20.10 | 20.10 | December 2024 |
| RHEL 8 | 8.x | May 2029 |

### Upgrade Paths

- Minor versions: In-place upgrade supported
- Major versions: Migration procedure required
- LTS releases: Recommended for production
- Security updates: Applied monthly

---

*For detailed installation procedures, refer to the Installation Guide.*  
*For performance optimization, consult the Administrator's Guide.*