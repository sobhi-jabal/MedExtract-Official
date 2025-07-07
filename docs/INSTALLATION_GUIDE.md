# MedExtract Installation Guide

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Pre-Installation Planning](#pre-installation-planning)
3. [System Requirements](#system-requirements)
4. [Windows Installation](#windows-installation)
5. [macOS Installation](#macos-installation)
6. [Linux Installation](#linux-installation)
7. [Enterprise Network Configuration](#enterprise-network-configuration)
8. [Post-Installation Configuration](#post-installation-configuration)
9. [Validation and Testing](#validation-and-testing)
10. [Troubleshooting](#troubleshooting)
11. [Maintenance and Updates](#maintenance-and-updates)

## Executive Summary

This guide provides comprehensive instructions for installing MedExtract in healthcare IT environments. The installation process requires administrative privileges and coordination with security and network teams. Total installation time ranges from 30-90 minutes depending on network conditions and system configuration.

### Installation Overview
1. Verify system requirements
2. Install prerequisite software
3. Configure network and security settings
4. Deploy MedExtract components
5. Validate installation
6. Configure for production use

## Pre-Installation Planning

### Stakeholder Coordination

| Stakeholder | Responsibility | Required Actions |
|-------------|---------------|------------------|
| IT Security | Security approval | Review architecture, approve firewall rules |
| Network Team | Network configuration | Configure proxy, open required ports |
| System Admin | Server preparation | Provision resources, install prerequisites |
| Clinical IT | Integration planning | Coordinate with clinical systems |
| Compliance | HIPAA assessment | Review data handling procedures |

### Infrastructure Assessment

#### Network Requirements
- [ ] Internet connectivity for initial setup (can be temporary)
- [ ] Internal network access for users
- [ ] Proxy configuration if applicable
- [ ] Firewall rule modifications
- [ ] DNS resolution for container registry

#### Security Considerations
- [ ] Antivirus exclusions may be required
- [ ] Administrator/sudo access needed
- [ ] Service account creation
- [ ] Certificate management for HTTPS

## System Requirements

*Detailed requirements are available in [SYSTEM_REQUIREMENTS.md](SYSTEM_REQUIREMENTS.md)*

### Quick Reference

| Component | Minimum | Recommended | Enterprise |
|-----------|---------|-------------|------------|
| CPU | 4 cores | 8 cores | 16+ cores |
| RAM | 16 GB | 32 GB | 64+ GB |
| Storage | 50 GB SSD | 250 GB NVMe | 1 TB NVMe |
| OS | Win 10 Pro | Win Server 2019 | RHEL 8+ |

## Windows Installation

### Prerequisites Installation

#### 1. Docker Desktop Installation

```powershell
# Download Docker Desktop
# https://www.docker.com/products/docker-desktop/

# Verify installation
docker --version
docker-compose --version
```

**Docker Configuration**:
1. Open Docker Desktop settings
2. Resources → Advanced:
   - CPUs: 4 (minimum)
   - Memory: 8 GB (minimum)
   - Disk image size: 64 GB
3. Apply & Restart

#### 2. Enable Required Windows Features

```powershell
# Run as Administrator
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
```

### Automated Installation

#### Step 1: Download Installer

1. Navigate to [Releases](https://github.com/your-org/MedExtract-Official/releases)
2. Download `MedExtract-Windows-x64-v1.0.0-Installer.exe`
3. Verify checksum:
   ```powershell
   CertUtil -hashfile MedExtract-Windows-x64-v1.0.0-Installer.exe SHA256
   # Compare with published checksum
   ```

#### Step 2: Pre-Installation Checks

```powershell
# Run as Administrator
# Check system requirements
systeminfo | findstr /C:"Total Physical Memory" /C:"Available Physical Memory"
wmic cpu get NumberOfCores,NumberOfLogicalProcessors

# Verify Docker
docker system info
```

#### Step 3: Execute Installation

1. **Right-click** installer → **Run as administrator**
2. **Installation Wizard**:
   - Accept license agreement
   - Choose installation directory (default: `C:\Program Files\MedExtract`)
   - Select components:
     - [x] Core Application
     - [x] Language Models (20 GB)
     - [ ] Sample Data (optional)
   - Configure network settings if prompted

3. **Installation Progress**:
   ```
   Phase 1: System verification (1-2 minutes)
   Phase 2: Component download (5-15 minutes)
   Phase 3: Container build (10-20 minutes)
   Phase 4: Service configuration (2-3 minutes)
   Phase 5: Health check (1-2 minutes)
   ```

#### Step 4: Service Configuration

```powershell
# Verify services are running
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Expected output:
# NAMES                STATUS              PORTS
# medextract-frontend  Up 2 minutes        0.0.0.0:3000->3000/tcp
# medextract-backend   Up 2 minutes        0.0.0.0:8000->8000/tcp
# ollama               Up 2 minutes        0.0.0.0:11434->11434/tcp
```

## macOS Installation

### Prerequisites

#### 1. Install Docker Desktop

```bash
# Using Homebrew
brew install --cask docker

# Or download from https://www.docker.com/products/docker-desktop/

# Start Docker Desktop
open -a Docker

# Verify installation
docker --version
```

#### 2. System Configuration

```bash
# Increase Docker resources
# Docker Desktop → Preferences → Resources:
# - CPUs: 4+
# - Memory: 8+ GB
# - Disk: 64+ GB
```

### Installation Process

```bash
# 1. Download installer
curl -L -o MedExtract-macOS-Universal-v1.0.0.tar.gz \
  https://github.com/your-org/MedExtract-Official/releases/download/v1.0.0/MedExtract-macOS-Universal-v1.0.0.tar.gz

# 2. Verify checksum
shasum -a 256 MedExtract-macOS-Universal-v1.0.0.tar.gz

# 3. Extract archive
tar -xzf MedExtract-macOS-Universal-v1.0.0.tar.gz
cd MedExtract-v1.0.0

# 4. Run installer
sudo ./installer/install.sh

# 5. Follow prompts for configuration
```

## Linux Installation

### Distribution-Specific Prerequisites

#### Ubuntu/Debian

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### RHEL/CentOS

```bash
# Install Docker
sudo yum install -y docker docker-compose
sudo systemctl enable docker
sudo systemctl start docker

# Configure SELinux
sudo setsebool -P container_manage_cgroup on
```

### Installation Process

```bash
# 1. Download and extract
wget https://github.com/your-org/MedExtract-Official/releases/download/v1.0.0/MedExtract-Linux-x64-v1.0.0.tar.gz
tar -xzf MedExtract-Linux-x64-v1.0.0.tar.gz
cd MedExtract-v1.0.0

# 2. Run installer
sudo ./installer/install.sh --production

# 3. Configure systemd service
sudo cp config/medextract.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable medextract
sudo systemctl start medextract
```

## Enterprise Network Configuration

### Proxy Configuration

#### Automatic Detection

The installer attempts to detect proxy settings from:
1. System environment variables
2. Registry (Windows)
3. Network configuration files

#### Manual Configuration

```bash
# Create environment file
cat > .env << EOF
# Proxy Configuration
HTTP_PROXY=http://proxy.institution.edu:8080
HTTPS_PROXY=http://proxy.institution.edu:8080
NO_PROXY=localhost,127.0.0.1,*.institution.edu

# Certificate Bundle (if required)
REQUESTS_CA_BUNDLE=/etc/ssl/certs/institution-ca-bundle.crt
SSL_CERT_FILE=/etc/ssl/certs/institution-ca-bundle.crt
EOF
```

### Firewall Configuration

#### Required Ports

| Port | Direction | Purpose | Protocol |
|------|-----------|---------|----------|
| 3000 | Inbound | Web Interface | TCP |
| 8000 | Inbound | API Access | TCP |
| 443 | Outbound | HTTPS (setup only) | TCP |
| 80 | Outbound | HTTP (setup only) | TCP |

#### Firewall Rules (Example)

```bash
# Windows Firewall
netsh advfirewall firewall add rule name="MedExtract Web" dir=in action=allow protocol=TCP localport=3000
netsh advfirewall firewall add rule name="MedExtract API" dir=in action=allow protocol=TCP localport=8000

# Linux iptables
sudo iptables -A INPUT -p tcp --dport 3000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables-save
```

### Certificate Management

#### Self-Signed Certificates (Development)

```bash
# Generate certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout medextract.key \
  -out medextract.crt \
  -subj "/C=US/ST=State/L=City/O=Institution/CN=medextract.local"
```

#### Enterprise CA Certificates

```bash
# Import institution CA
sudo cp institution-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# Configure Docker to trust CA
sudo mkdir -p /etc/docker/certs.d/registry.institution.edu
sudo cp institution-ca.crt /etc/docker/certs.d/registry.institution.edu/ca.crt
sudo systemctl restart docker
```

## Post-Installation Configuration

### Initial Configuration

#### 1. Access Web Interface

```bash
# Default URLs
http://localhost:3000  # Production
http://localhost:3000/admin  # Administration
```

#### 2. Configure Authentication

```yaml
# config/auth.yaml
authentication:
  type: ldap  # or: basic, saml, oauth2
  ldap:
    server: ldap://directory.institution.edu
    base_dn: dc=institution,dc=edu
    user_dn: cn=users,dc=institution,dc=edu
    bind_dn: cn=medextract,cn=services,dc=institution,dc=edu
    bind_password: ${LDAP_BIND_PASSWORD}
```

#### 3. Model Configuration

```bash
# Pull required models
docker exec -it ollama ollama pull phi4:latest
docker exec -it ollama ollama pull llama2:13b

# Verify models
docker exec -it ollama ollama list
```

### Performance Tuning

#### CPU-Only Configuration

```yaml
# docker-compose.override.yml
services:
  backend:
    environment:
      - NUM_WORKERS=4
      - BATCH_SIZE=10
      - MODEL_THREADS=8
```

#### GPU-Enabled Configuration

```yaml
# docker-compose.override.yml
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## Validation and Testing

### System Health Checks

#### 1. Service Verification

```bash
# Check all services are running
curl -f http://localhost:8000/health || echo "Backend not responding"
curl -f http://localhost:3000 || echo "Frontend not responding"
curl -f http://localhost:11434 || echo "Ollama not responding"

# Comprehensive health check
docker exec medextract-backend python -m medextract.health_check
```

#### 2. Component Testing

```bash
# Test model inference
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "phi4:latest", "prompt": "Test"}'

# Test API endpoints
curl http://localhost:8000/api/v1/models
curl http://localhost:8000/api/v1/system/info
```

### Functional Validation

#### Test Extraction Job

1. **Prepare test data** (`test_reports.csv`):
   ```csv
   report_id,report_text
   001,"Patient presents with acute chest pain. ECG shows ST elevation in leads II, III, aVF. Impression: Acute inferior myocardial infarction."
   002,"Chest X-ray reveals no acute cardiopulmonary process. Lungs are clear. Heart size normal."
   ```

2. **Configure extraction**:
   - Upload test file
   - Add datapoint: "diagnosis"
   - Run extraction
   - Verify results

3. **Expected output**:
   ```csv
   report_id,report_text,diagnosis_extracted
   001,"...","Acute inferior myocardial infarction"
   002,"...","No acute cardiopulmonary process"
   ```

### Performance Validation

```bash
# Benchmark processing speed
time docker exec medextract-backend python -m medextract.benchmark \
  --reports 100 \
  --model phi4:latest

# Monitor resource usage
docker stats --no-stream
```

## Troubleshooting

### Common Installation Issues

#### Docker Desktop Not Running

**Symptoms**: Installation fails with "Docker daemon not running"

**Resolution**:
```powershell
# Windows
Start-Service docker
Start-Process "Docker Desktop.exe"

# macOS/Linux
sudo systemctl start docker
```

#### Insufficient Resources

**Symptoms**: Container crashes or fails to start

**Resolution**:
1. Increase Docker resource allocation
2. Check available disk space
3. Close unnecessary applications

#### Network Connectivity Issues

**Symptoms**: Failed to pull images, timeout errors

**Resolution**:
```bash
# Test connectivity
docker pull hello-world

# Configure proxy if needed
export HTTP_PROXY=http://proxy:8080
export HTTPS_PROXY=http://proxy:8080
```

### Model Download Failures

#### Certificate Errors

**Symptoms**: "x509: certificate signed by unknown authority"

**Resolution**:
```bash
# Option 1: Install Ollama locally
# https://ollama.ai/download

# Option 2: Configure certificate bundle
export SSL_CERT_FILE=/path/to/ca-bundle.crt
```

#### Disk Space Issues

**Symptoms**: "no space left on device"

**Resolution**:
```bash
# Clean Docker resources
docker system prune -a --volumes

# Check disk usage
df -h
docker system df
```

### Service Access Problems

#### Port Conflicts

**Symptoms**: "bind: address already in use"

**Resolution**:
```bash
# Find process using port
netstat -tulpn | grep :3000
lsof -i :3000

# Change port in docker-compose.yml
ports:
  - "3001:3000"  # Changed from 3000
```

#### Firewall Blocking

**Symptoms**: Cannot access web interface

**Resolution**:
- Check firewall rules
- Verify Docker network settings
- Test with localhost first

## Maintenance and Updates

### Regular Maintenance Tasks

#### Daily
- Monitor disk usage
- Check service health
- Review error logs

#### Weekly
- Apply security updates
- Backup configurations
- Clear old log files

#### Monthly
- Update Docker images
- Review resource usage
- Performance analysis

### Update Procedures

#### Minor Updates (1.0.x)

```bash
# Stop services
docker-compose down

# Pull latest images
docker-compose pull

# Start services
docker-compose up -d

# Verify update
docker exec medextract-backend python -m medextract.version
```

#### Major Updates (x.0.0)

1. **Backup current installation**
   ```bash
   tar -czf medextract-backup-$(date +%Y%m%d).tar.gz \
     ./config ./data ./docker-compose.yml
   ```

2. **Review migration notes**
3. **Test in non-production environment**
4. **Schedule maintenance window**
5. **Execute migration procedure**

### Backup and Recovery

#### Backup Strategy

```bash
#!/bin/bash
# backup-medextract.sh

BACKUP_DIR="/backup/medextract"
DATE=$(date +%Y%m%d_%H%M%S)

# Stop services
docker-compose stop

# Backup data
tar -czf "$BACKUP_DIR/medextract-data-$DATE.tar.gz" ./data
tar -czf "$BACKUP_DIR/medextract-config-$DATE.tar.gz" ./config

# Backup database (if applicable)
docker-compose exec -T postgres pg_dump -U medextract > "$BACKUP_DIR/medextract-db-$DATE.sql"

# Start services
docker-compose start

# Retention policy (keep 30 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

#### Recovery Procedure

1. Stop current services
2. Restore configuration files
3. Restore data directory
4. Import database (if applicable)
5. Start services
6. Validate functionality

### Monitoring and Alerting

#### Health Check Script

```bash
#!/bin/bash
# health-check.sh

# Check services
for service in frontend backend ollama; do
  if ! docker ps | grep -q "medextract-$service"; then
    echo "ALERT: $service is not running"
    # Send alert (email, SMS, etc.)
  fi
done

# Check disk space
USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $USAGE -gt 80 ]; then
  echo "ALERT: Disk usage is $USAGE%"
fi

# Check API health
if ! curl -f -s http://localhost:8000/health > /dev/null; then
  echo "ALERT: API health check failed"
fi
```

---

*For additional support, consult the [System Requirements](SYSTEM_REQUIREMENTS.md) and [Troubleshooting](TROUBLESHOOTING.md) guides.*