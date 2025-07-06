# MedExtract User Guide

## Overview

MedExtract is designed to extract structured data from unstructured medical reports using advanced language models. This guide will walk you through using the platform effectively.

## Getting Started

### Accessing MedExtract

1. **Start the Application**
   - Use the desktop shortcut `MedExtract.bat`
   - Or navigate to http://localhost:3000

2. **Initial Setup**
   - The application will check system health
   - Download required models if needed
   - Show the main dashboard

### Understanding the Interface

The MedExtract interface consists of:
- **Dashboard**: Overview of extraction jobs
- **Create Job**: Configure new extractions
- **Job Details**: Monitor progress and results
- **Models**: Manage LLM models

## Creating an Extraction Job

### Step 1: Upload Data

1. **Click "Create New Job"**
2. **Select your data file**
   - Supported formats: CSV, Excel (.xlsx, .xls)
   - Maximum file size: 500MB
   - Must contain a text column with reports

3. **Preview your data**
   - First 10 rows displayed
   - Verify column selection
   - Check data quality

### Step 2: Configure Columns

1. **Select Text Column**
   - Choose the column containing medical reports
   - Usually named "Report", "Text", or similar

2. **Optional: Ground Truth Column**
   - For validation and metrics
   - Select if you have labeled data

### Step 3: Define Datapoints

1. **Add Datapoints to Extract**
   - Click "Add Datapoint"
   - Provide clear names (e.g., "diagnosis", "medication")

2. **Configure Each Datapoint**
   ```
   Name: diagnosis
   Instruction: Extract the primary diagnosis from the report
   Query Terms: diagnosis, dx, impression, findings
   Default Value: Not Reported
   ```

3. **Use Presets (Optional)**
   - Indications & Impressions
   - BT-RADS Assessment
   - NIH Grant Analysis

### Step 4: Configure Extraction Settings

#### Model Selection
- **phi4:latest**: Balanced performance and accuracy
- **llama2:latest**: Good for general medical text
- **mistral:latest**: Fast, good for simple extractions

#### RAG Settings
- **Enable RAG**: For complex, context-dependent extractions
- **Chunk Size**: 800 (default) - adjust based on report length
- **Chunk Overlap**: 150 - ensures context continuity

#### Generation Parameters
- **Temperature**: 0.1 (low = consistent, high = creative)
- **Top K**: 40 - limits vocabulary selection
- **Top P**: 0.9 - nucleus sampling threshold

#### Processing Options
- **Batch Size**: 5 - reports processed simultaneously
- **Save Intermediate**: Enable for long jobs
- **Save Frequency**: Every 10 reports

### Step 5: Start Extraction

1. **Review Configuration**
2. **Click "Start Extraction"**
3. **Monitor Progress**
   - Real-time progress bar
   - Current report being processed
   - Estimated time remaining

## Monitoring Extraction Progress

### Real-time Updates
- Progress percentage
- Current row/total rows
- Processing speed
- Error notifications

### Pause/Resume
- Click "Pause" to temporarily stop
- Resume maintains progress
- Safe to close browser

### Handling Errors
- Automatic retry for transient errors
- Skip problematic reports
- Download partial results

## Downloading Results

### Available Formats
1. **CSV Format**
   - Compatible with Excel, R, Python
   - Includes all extracted datapoints
   - Original data preserved

2. **Excel Format**
   - Formatted spreadsheet
   - Multiple sheets if needed
   - Ready for analysis

### Result Structure
```
Original Columns | Extracted Datapoints | Metadata
Report_ID       | diagnosis_extracted  | extraction_time
Report_Text     | medication_extracted | confidence_score
...             | ...                  | ...
```

## Advanced Features

### Using Few-Shot Examples

Improve extraction accuracy with examples:

1. **Enable Few-Shot Learning**
2. **Provide Examples**
   ```json
   {
     "text": "Patient diagnosed with pneumonia...",
     "diagnosis": "Pneumonia"
   }
   ```

### Extraction Strategies

1. **Single Call** (Default)
   - All datapoints in one prompt
   - Faster, good for related datapoints

2. **Sequential**
   - One datapoint at a time
   - More accurate for complex extractions

3. **Parallel**
   - Multiple datapoints simultaneously
   - Balanced speed and accuracy

### Custom Validation

Define valid values for structured data:
```
Valid Values: ["Positive", "Negative", "Inconclusive"]
```

## Best Practices

### Data Preparation
- Clean text data (remove special characters if needed)
- Consistent formatting
- Sufficient text content

### Datapoint Design
- Clear, specific instructions
- Relevant query terms
- Appropriate default values
- Test with small batches first

### Performance Optimization
- Use appropriate batch sizes
- Enable intermediate saves for large jobs
- Monitor system resources
- Choose right model for complexity

### Quality Assurance
- Validate with ground truth
- Review sample extractions
- Iterate on instructions
- Use few-shot examples

## Troubleshooting

### Slow Performance
- Reduce batch size
- Use simpler model
- Check system resources
- Disable RAG if not needed

### Poor Accuracy
- Improve instructions
- Add few-shot examples
- Enable RAG
- Try different model

### Memory Issues
- Process in smaller batches
- Enable intermediate saves
- Restart Docker containers
- Increase Docker resources

## Model Management

### Available Models
- View in Models section
- Check download status
- See model details

### Downloading Models
1. Click "Pull Model"
2. Enter model name
3. Monitor download progress
4. Wait for completion

### Switching Models
- Select during job creation
- Different models for different tasks
- Balance speed vs accuracy

## Tips and Tricks

### For Medical Reports
- Use domain-specific terms in queries
- Include section headers in instructions
- Handle abbreviations explicitly

### For Research Data
- Standardize output formats
- Use consistent naming conventions
- Document extraction logic

### For Large Datasets
- Process in chunks
- Use checkpoint feature
- Monitor overnight jobs
- Set up email notifications

## Getting Help

### In-App Resources
- Tooltip help icons
- Example configurations
- Preset templates

### External Resources
- GitHub documentation
- Video tutorials
- Community forum
- Support email

## Next Steps

1. Try a sample extraction
2. Experiment with settings
3. Build your extraction pipeline
4. Share results with team