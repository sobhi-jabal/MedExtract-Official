# MedExtract Troubleshooting Guide

## Table of Contents
1. [Quick Diagnostics](#quick-diagnostics)
2. [Installation Issues](#installation-issues)
3. [Clinical Data Processing Issues](#clinical-data-processing-issues)
4. [Performance Problems](#performance-problems)
5. [Network and Connectivity](#network-and-connectivity)
6. [Model-Related Issues](#model-related-issues)
7. [Data Quality Issues](#data-quality-issues)
8. [Security and Access Issues](#security-and-access-issues)
9. [Clinical Workflow Integration](#clinical-workflow-integration)
10. [Advanced Diagnostics](#advanced-diagnostics)

## Quick Diagnostics

### System Health Check

Run this comprehensive diagnostic to identify common issues:

```bash
#!/bin/bash
# medextract-diagnostic.sh

echo "=== MedExtract System Diagnostic ==="
echo "Date: $(date)"
echo ""

# Check Docker
echo "1. Docker Status:"
docker --version || echo "ERROR: Docker not installed"
docker ps >/dev/null 2>&1 || echo "ERROR: Docker daemon not running"

# Check Services
echo -e "\n2. Service Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep medextract

# Check Connectivity
echo -e "\n3. Service Health:"
curl -s http://localhost:8000/health | jq '.' || echo "Backend not responding"
curl -s http://localhost:3000 >/dev/null && echo "Frontend: OK" || echo "Frontend: NOT RESPONDING"

# Check Resources
echo -e "\n4. Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Check Disk Space
echo -e "\n5. Disk Space:"
df -h / | grep -v Filesystem

# Check Logs for Errors
echo -e "\n6. Recent Errors:"
docker logs medextract-backend 2>&1 | grep -i error | tail -5
```

### Common Quick Fixes

| Symptom | Quick Fix | Command |
|---------|-----------|---------|
| Services not running | Restart all services | `docker-compose restart` |
| Out of memory | Clear Docker cache | `docker system prune -a` |
| Port conflict | Change port mapping | Edit `docker-compose.yml` |
| Slow processing | Check resource allocation | `docker stats` |

## Installation Issues

### Docker Installation Problems

#### Issue: Docker Desktop Not Starting (Windows)

**Symptoms**: 
- Docker Desktop icon shows "Starting..." indefinitely
- Error: "Docker Desktop - WSL kernel version too low"

**Clinical Impact**: Cannot begin installation of MedExtract

**Resolution**:
```powershell
# Run as Administrator
# 1. Update WSL
wsl --update

# 2. Enable virtualization
bcdedit /set hypervisorlaunchtype auto

# 3. Restart computer
Restart-Computer

# 4. Reset Docker Desktop
Remove-Item -Path "$env:APPDATA\Docker" -Recurse -Force
Remove-Item -Path "$env:LOCALAPPDATA\Docker" -Recurse -Force
```

#### Issue: Insufficient Privileges

**Symptoms**: 
- "Permission denied" errors
- Cannot create directories or files

**Clinical Impact**: Installation cannot proceed

**Resolution**:
```bash
# Linux/macOS
sudo usermod -aG docker $USER
newgrp docker

# Windows - Run as Administrator
net localgroup docker-users "%USERNAME%" /add
```

### Installation Failures

#### Issue: Model Download Timeout

**Symptoms**:
- Installation hangs at "Downloading language models"
- Network timeout errors

**Clinical Impact**: Cannot process medical reports without models

**Resolution**:
```bash
# Option 1: Increase timeout
export OLLAMA_DOWNLOAD_TIMEOUT=3600

# Option 2: Manual download
docker exec -it ollama bash
ollama pull phi4:latest --insecure

# Option 3: Use pre-downloaded models
docker cp ./models/phi4.bin ollama:/root/.ollama/models/
```

## Clinical Data Processing Issues

### Report Extraction Failures

#### Issue: Empty Extraction Results

**Symptoms**:
- All extracted fields show "Not Found" or empty
- No error messages displayed

**Clinical Context**: Common with poorly formatted radiology or pathology reports

**Diagnosis**:
```python
# Check report format
import pandas as pd
df = pd.read_csv('reports.csv')
print(f"Column names: {df.columns.tolist()}")
print(f"Sample text: {df.iloc[0]['report_text'][:200]}")
```

**Resolution**:
1. **Verify text column selection**
2. **Check for encoding issues**:
   ```bash
   file -i reports.csv
   iconv -f ISO-8859-1 -t UTF-8 reports.csv > reports_utf8.csv
   ```
3. **Improve extraction instructions**:
   - Add more specific clinical terms
   - Include section headers in query terms
   - Provide few-shot examples

#### Issue: Inconsistent Extraction Results

**Symptoms**:
- Same report yields different results
- Extraction accuracy varies significantly

**Clinical Context**: Critical for research data integrity

**Resolution**:
```yaml
# Adjust model parameters for consistency
extraction_config:
  temperature: 0.1  # Lower = more consistent
  top_p: 0.9
  seed: 42  # Set fixed seed
  num_ctx: 2048  # Ensure sufficient context
```

### Data Format Issues

#### Issue: Special Characters in Medical Reports

**Symptoms**:
- Extraction fails on reports with symbols (°, ±, μ)
- Unicode decode errors

**Clinical Context**: Common in lab reports and measurements

**Resolution**:
```python
# Preprocessing script
import pandas as pd
import ftfy  # fixes text encoding

def clean_medical_text(text):
    # Fix encoding
    text = ftfy.fix_text(text)
    # Preserve medical symbols
    replacements = {
        '°': ' degrees',
        '±': ' plus-minus',
        'μ': 'micro'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

df['report_text'] = df['report_text'].apply(clean_medical_text)
```

## Performance Problems

### Slow Processing Speed

#### Issue: Reports Processing Too Slowly

**Symptoms**:
- Processing rate < 50 reports/hour
- Long delays between reports

**Clinical Impact**: Delays in research data availability

**Diagnosis**:
```bash
# Check system bottlenecks
docker exec medextract-backend python -c "
import psutil
print(f'CPU cores: {psutil.cpu_count()}')
print(f'RAM available: {psutil.virtual_memory().available / 1e9:.1f} GB')
print(f'CPU usage: {psutil.cpu_percent(interval=1)}%')
"
```

**Resolution by Configuration**:

| Setup | Expected Speed | Optimization |
|-------|---------------|--------------|
| CPU-only | 100-200/hour | Reduce batch size, use smaller model |
| GPU-enabled | 300-500/hour | Increase batch size, check GPU utilization |
| Multi-GPU | 1000+/hour | Enable parallel processing |

### Memory Issues

#### Issue: Out of Memory Errors

**Symptoms**:
- Container crashes with "OOMKilled"
- System becomes unresponsive

**Clinical Context**: Occurs with large pathology report batches

**Resolution**:
```yaml
# docker-compose.override.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          memory: 8G
    environment:
      - MAX_BATCH_SIZE=25  # Reduce from 50
      - ENABLE_MEMORY_EFFICIENT_MODE=true
```

## Network and Connectivity

### Corporate Network Issues

#### Issue: TLS Certificate Errors

**Symptoms**:
- "x509: certificate signed by unknown authority"
- Cannot download models or updates

**Clinical Context**: Common in hospital networks with SSL inspection

**Resolution**:
```bash
# Option 1: Configure certificate bundle
export NODE_EXTRA_CA_CERTS=/path/to/hospital-ca-bundle.crt
export REQUESTS_CA_BUNDLE=/path/to/hospital-ca-bundle.crt
export SSL_CERT_FILE=/path/to/hospital-ca-bundle.crt

# Option 2: Docker configuration
mkdir -p /etc/docker/certs.d/registry.hospital.edu
cp hospital-ca.crt /etc/docker/certs.d/registry.hospital.edu/ca.crt
systemctl restart docker
```

#### Issue: Proxy Authentication Required

**Symptoms**:
- "407 Proxy Authentication Required"
- Cannot reach external resources

**Clinical Context**: Hospital IT security requirements

**Resolution**:
```bash
# Set authenticated proxy
export HTTP_PROXY=http://username:password@proxy.hospital.edu:8080
export HTTPS_PROXY=http://username:password@proxy.hospital.edu:8080
export NO_PROXY=localhost,127.0.0.1,*.hospital.local

# For Docker
cat > ~/.docker/config.json << EOF
{
  "proxies": {
    "default": {
      "httpProxy": "http://proxy.hospital.edu:8080",
      "httpsProxy": "http://proxy.hospital.edu:8080",
      "noProxy": "localhost,127.0.0.1"
    }
  }
}
EOF
```

## Model-Related Issues

### Model Loading Failures

#### Issue: Model Not Found

**Symptoms**:
- Error: "model 'phi4:latest' not found"
- Extraction fails immediately

**Clinical Impact**: Cannot process any reports

**Resolution**:
```bash
# List available models
docker exec ollama ollama list

# Pull required model
docker exec ollama ollama pull phi4:latest

# Verify model loaded
docker exec ollama ollama run phi4:latest "test"
```

### Model Performance Issues

#### Issue: Poor Extraction Accuracy

**Symptoms**:
- Extraction accuracy < 80%
- Missing obvious clinical findings

**Clinical Context**: Different models perform better for specific report types

**Model Selection Guide**:

| Report Type | Recommended Model | Rationale |
|-------------|------------------|-----------|
| Radiology | phi4:latest | Optimized for medical terminology |
| Pathology | llama2:13b | Better with complex narratives |
| Clinical Notes | mistral:7b | Faster for simple extractions |
| Multi-lingual | llama2:70b | Supports non-English text |

## Data Quality Issues

### Input Data Problems

#### Issue: Malformed CSV Files

**Symptoms**:
- "Error reading CSV file"
- Pandas parsing errors

**Clinical Context**: Exported data from EMR systems may have formatting issues

**Diagnostic Script**:
```python
import pandas as pd
import chardet

# Detect encoding
with open('reports.csv', 'rb') as f:
    result = chardet.detect(f.read(10000))
    print(f"Detected encoding: {result['encoding']}")

# Try reading with different parameters
try:
    df = pd.read_csv('reports.csv', encoding=result['encoding'])
except:
    df = pd.read_csv('reports.csv', encoding='latin-1', error_bad_lines=False)

print(f"Successfully read {len(df)} rows")
print(f"Columns: {df.columns.tolist()}")
```

### Output Data Validation

#### Issue: Extraction Validation Failures

**Symptoms**:
- Extracted data doesn't match ground truth
- Inconsistent formatting

**Clinical Context**: Critical for research validity

**Validation Framework**:
```python
def validate_extraction(extracted, ground_truth):
    """Validate extraction against ground truth"""
    metrics = {
        'exact_match': extracted == ground_truth,
        'partial_match': ground_truth.lower() in extracted.lower(),
        'missing': pd.isna(extracted) and not pd.isna(ground_truth),
        'extra': not pd.isna(extracted) and pd.isna(ground_truth)
    }
    return metrics

# Apply validation
validation_results = df.apply(
    lambda row: validate_extraction(
        row['diagnosis_extracted'], 
        row['diagnosis_ground_truth']
    ), 
    axis=1
)
```

## Security and Access Issues

### Authentication Problems

#### Issue: Cannot Log In

**Symptoms**:
- "Invalid credentials" despite correct password
- Session expires immediately

**Clinical Context**: Compliance with hospital security policies

**Resolution**:
```yaml
# Check authentication configuration
# config/auth.yaml
authentication:
  session_timeout: 3600  # Increase from default
  max_attempts: 5
  lockout_duration: 300
  
# For LDAP issues
ldap:
  server: ldaps://hospital-dc.hospital.local:636
  bind_dn: "CN=medextract,OU=ServiceAccounts,DC=hospital,DC=local"
  search_base: "OU=Users,DC=hospital,DC=local"
  user_filter: "(sAMAccountName={username})"
```

### Access Control Issues

#### Issue: Unauthorized Access to PHI

**Symptoms**:
- Users can see data they shouldn't
- Audit logs show inappropriate access

**Clinical Context**: HIPAA violation risk

**Resolution**:
```bash
# Implement role-based access
docker exec medextract-backend python manage.py create_role researcher \
  --permissions view_own_jobs,create_jobs,download_results

docker exec medextract-backend python manage.py assign_role \
  --user john.doe@hospital.edu --role researcher
```

## Clinical Workflow Integration

### EMR Integration Issues

#### Issue: Cannot Export Reports from EMR

**Symptoms**:
- EMR export function disabled
- Format incompatible with MedExtract

**Clinical Context**: Hospital IT restrictions

**Workaround Solutions**:

1. **Manual Export Process**:
   ```sql
   -- Example Epic Clarity query
   SELECT 
     PAT_ID,
     REPORT_TEXT,
     REPORT_DATE
   FROM RADIOLOGY_REPORTS
   WHERE REPORT_DATE >= '2024-01-01'
   ```

2. **Automated Export Script**:
   ```python
   # Schedule this to run nightly
   import pyodbc
   import pandas as pd
   
   conn = pyodbc.connect('DSN=EMR_PROD;UID=svc_account;PWD=xxx')
   query = "SELECT * FROM CLINICAL_REPORTS WHERE STATUS='FINAL'"
   df = pd.read_sql(query, conn)
   df.to_csv('/export/daily_reports.csv', index=False)
   ```

### Result Integration Issues

#### Issue: Cannot Import Results Back to EMR

**Symptoms**:
- Structured data not accepted by EMR
- Format mismatch errors

**Clinical Context**: Need for clinical decision support

**Resolution**:
```python
# Transform results to EMR-compatible format
def format_for_emr(extracted_df):
    """Convert MedExtract output to EMR format"""
    emr_format = pd.DataFrame()
    emr_format['PATIENT_ID'] = extracted_df['report_id']
    emr_format['EXTRACTED_DATE'] = pd.Timestamp.now()
    emr_format['DIAGNOSIS_CODE'] = map_to_icd10(extracted_df['diagnosis'])
    emr_format['CONFIDENCE'] = extracted_df['confidence_score']
    
    return emr_format
```

## Advanced Diagnostics

### Debug Mode

Enable comprehensive debugging:

```bash
# Set debug environment
export MEDEXTRACT_DEBUG=true
export LOG_LEVEL=DEBUG

# Restart services with debug logging
docker-compose down
docker-compose up
```

### Performance Profiling

```python
# Profile extraction performance
docker exec medextract-backend python -m cProfile -o profile.out \
  medextract.extract --input test.csv --output results.csv

# Analyze profile
docker exec medextract-backend python -c "
import pstats
p = pstats.Stats('profile.out')
p.sort_stats('cumulative').print_stats(20)
"
```

### Log Analysis

```bash
# Aggregate logs for analysis
docker-compose logs --tail=1000 > medextract_logs.txt

# Common error patterns
grep -E "(ERROR|CRITICAL|Exception)" medextract_logs.txt | \
  awk '{print $5}' | sort | uniq -c | sort -nr

# Response time analysis
grep "Request completed" medextract_logs.txt | \
  awk '{print $NF}' | \
  awk '{sum+=$1; count++} END {print "Avg response time:", sum/count, "ms"}'
```

### Container Diagnostics

```bash
# Detailed container inspection
docker inspect medextract-backend > backend_inspect.json

# Check container health
docker exec medextract-backend cat /proc/1/status

# Network diagnostics
docker exec medextract-backend netstat -tuln
docker exec medextract-backend nslookup ollama
```

## Getting Help

### Support Escalation Path

1. **Level 1**: Check this troubleshooting guide
2. **Level 2**: Review application logs
3. **Level 3**: Contact IT support team
4. **Level 4**: Submit GitHub issue with diagnostic output
5. **Level 5**: Schedule support call with development team

### Information to Provide

When requesting support, include:

```bash
# Generate support bundle
./generate-support-bundle.sh

# This collects:
# - System information
# - Service status
# - Recent logs (sanitized)
# - Configuration (without secrets)
# - Performance metrics
```

### Clinical IT Contact

For urgent clinical workflow issues:
- Email: medextract-support@institution.edu
- Phone: Extension 12345 (Business hours)
- On-call: Pager 67890 (After hours, critical only)

---

*Last Updated: [Current Date]*  
*Version: 1.0*  
*For clinical emergencies, follow standard hospital IT escalation procedures*