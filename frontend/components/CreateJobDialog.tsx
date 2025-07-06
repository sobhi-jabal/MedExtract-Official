"use client";

import { useState, useCallback, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useDropzone } from "react-dropzone";
import { Plus, Upload, X, FileText, Settings, Brain, Database } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { modelsAPI, jobsAPI, configAPI, type JobRequest, type DatapointConfig } from "@/lib/api";

interface CreateJobDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onJobCreated: () => void;
}

export function CreateJobDialog({ open, onOpenChange, onJobCreated }: CreateJobDialogProps) {
  const [step, setStep] = useState(1);
  const [jobName, setJobName] = useState("");
  const [textColumn, setTextColumn] = useState("");
  const [groundTruthColumn, setGroundTruthColumn] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [fileColumns, setFileColumns] = useState<string[]>([]);
  const [datapoints, setDatapoints] = useState<DatapointConfig[]>([{
    name: "",
    prompt: "",
    extraction_strategy: "single_call",
    output_format: "string",
    use_rag: false,
    confidence_threshold: 0.7
  }]);
  const [llmConfig, setLlmConfig] = useState({
    model_name: "",
    temperature: 0.1,
    max_tokens: 512,
    top_k: 40,
    top_p: 0.9,
    timeout: 60,
    max_retries: 3
  });
  const [processing, setProcessing] = useState(false);

  // Fetch available models
  const { data: modelsData, isLoading: modelsLoading, error: modelsError } = useQuery({
    queryKey: ['models'],
    queryFn: modelsAPI.list,
    enabled: open,
    retry: 3,
    retryDelay: 1000,
  });

  // Set default model when models data is loaded
  useEffect(() => {
    if (modelsData?.default_model && !llmConfig.model_name) {
      setLlmConfig(prev => ({ ...prev, model_name: modelsData.default_model }));
    }
  }, [modelsData, llmConfig.model_name]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    setFile(file);
    
    // Parse file to get columns (simplified - in real app, you'd parse properly)
    if (file.name.endsWith('.csv')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target?.result as string;
        const firstLine = text.split('\n')[0];
        const columns = firstLine.split(',').map(col => col.trim().replace(/"/g, ''));
        setFileColumns(columns);
      };
      reader.readAsText(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    multiple: false
  });

  const handleSubmit = async () => {
    if (!jobName || !textColumn || !file || (datapoints || []).length === 0) {
      alert("Please fill in all required fields");
      return;
    }

    setProcessing(true);
    try {
      // Create job request
      const jobRequest: JobRequest = {
        name: jobName,
        datapoint_configs: datapoints,
        processing_config: {
          batch_size: 10,
          max_workers: 4,
          timeout_per_item: 60,
          retry_attempts: 3,
          save_intermediate: true
        },
        llm_config: llmConfig.model_name ? llmConfig : undefined,
        rag_config: (datapoints || []).some(dp => dp.use_rag) ? {
          enabled: true,
          strategy: "semantic",
          chunk_size: 1000,
          chunk_overlap: 200,
          top_k: 5,
          embedding_model: "all-MiniLM-L6-v2",
          use_reranker: true,
          reranker_model: "BAAI/bge-reranker-v2-m3",
          reranker_top_n: 3
        } : undefined,
        text_column: textColumn,
        ground_truth_column: groundTruthColumn || undefined
      };

      // Debug log the request
      console.log('Job request being sent:', JSON.stringify(jobRequest, null, 2));
      
      // Validate configuration
      const validation = await configAPI.validate(jobRequest);
      if (!validation.valid) {
        alert(`Configuration errors: ${validation.errors.join(', ')}`);
        return;
      }

      // Create job
      const response = await jobsAPI.create(jobRequest);
      
      // Upload file
      await jobsAPI.uploadData(response.job_id, file);
      
      onJobCreated();
      resetForm();
    } catch (error: any) {
      console.error('Error creating job:', error);
      const errorMessage = error?.response?.data?.detail || error?.message || 'Unknown error occurred';
      alert(`Error creating job: ${errorMessage}. Please try again.`);
    } finally {
      setProcessing(false);
    }
  };

  const resetForm = () => {
    setStep(1);
    setJobName("");
    setTextColumn("");
    setGroundTruthColumn("");
    setFile(null);
    setFileColumns([]);
    setDatapoints([{
      name: "",
      prompt: "",
      extraction_strategy: "single_call",
      output_format: "string",
      use_rag: false,
      confidence_threshold: 0.7
    }]);
    setLlmConfig({
      model_name: "",
      temperature: 0.1,
      max_tokens: 512,
      top_k: 40,
      top_p: 0.9,
      timeout: 60,
      max_retries: 3
    });
  };

  const addDatapoint = () => {
    setDatapoints([...datapoints, {
      name: "",
      prompt: "",
      extraction_strategy: "single_call",
      output_format: "string",
      use_rag: false,
      confidence_threshold: 0.7
    }]);
  };

  const removeDatapoint = (index: number) => {
    setDatapoints(datapoints.filter((_, i) => i !== index));
  };

  const updateDatapoint = (index: number, field: string, value: any) => {
    const updated = [...datapoints];
    updated[index] = { ...updated[index], [field]: value };
    setDatapoints(updated);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">Create New Extraction Job</h2>
          <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="p-6">
          {/* Progress Steps */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              {[
                { step: 1, title: "Data Upload", icon: Upload },
                { step: 2, title: "Configuration", icon: Settings },
                { step: 3, title: "Review", icon: FileText }
              ].map(({ step: stepNum, title, icon: Icon }) => (
                <div key={stepNum} className="flex items-center">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                    step >= stepNum ? 'bg-blue-600 border-blue-600 text-white' : 'border-gray-300 text-gray-500'
                  }`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className={`ml-2 text-sm font-medium ${
                    step >= stepNum ? 'text-blue-600' : 'text-gray-500'
                  }`}>
                    {title}
                  </span>
                  {stepNum < 3 && (
                    <div className={`w-16 h-0.5 mx-4 ${
                      step > stepNum ? 'bg-blue-600' : 'bg-gray-300'
                    }`} />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Step 1: Data Upload */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Job Name *
                </label>
                <input
                  type="text"
                  value={jobName}
                  onChange={(e) => setJobName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., BT-RADS Extraction - Batch 1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload Data File *
                </label>
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                    isDragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <input {...getInputProps()} />
                  {file ? (
                    <div className="flex items-center justify-center space-x-2">
                      <FileText className="h-8 w-8 text-blue-600" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{file.name}</p>
                        <p className="text-xs text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-sm text-gray-600">
                        {isDragActive ? 'Drop the file here...' : 'Drag & drop a CSV or Excel file here, or click to select'}
                      </p>
                      <p className="text-xs text-gray-500 mt-2">Supports .csv, .xlsx, .xls files</p>
                    </div>
                  )}
                </div>
              </div>

              {fileColumns.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Text Column *
                    </label>
                    <select
                      value={textColumn}
                      onChange={(e) => setTextColumn(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select text column...</option>
                      {(fileColumns || []).map(col => (
                        <option key={col} value={col}>{col}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Ground Truth Column (Optional)
                    </label>
                    <select
                      value={groundTruthColumn}
                      onChange={(e) => setGroundTruthColumn(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select ground truth column...</option>
                      {(fileColumns || []).map(col => (
                        <option key={col} value={col}>{col}</option>
                      ))}
                    </select>
                  </div>
                </div>
              )}

              <div className="flex justify-end">
                <Button 
                  onClick={() => setStep(2)} 
                  disabled={!jobName || !file || !textColumn}
                  className="medical-gradient"
                >
                  Next: Configuration
                </Button>
              </div>
            </div>
          )}

          {/* Step 2: Configuration */}
          {step === 2 && (
            <div className="space-y-6">
              {/* Datapoints Configuration */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Database className="h-5 w-5 mr-2" />
                    Data Points to Extract
                  </CardTitle>
                  <CardDescription>
                    Define what information to extract from the medical text
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {(datapoints || []).map((datapoint, index) => (
                    <div key={index} className="border rounded-lg p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">Datapoint {index + 1}</h4>
                        {(datapoints || []).length > 1 && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeDatapoint(index)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <input
                          type="text"
                          placeholder="Datapoint name (e.g., BT-RADS)"
                          value={datapoint.name}
                          onChange={(e) => updateDatapoint(index, 'name', e.target.value)}
                          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <select
                          value={datapoint.extraction_strategy}
                          onChange={(e) => updateDatapoint(index, 'extraction_strategy', e.target.value)}
                          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="single_call">Single Call</option>
                          <option value="multi_call">Multi Call</option>
                          <option value="workflow">Workflow</option>
                        </select>
                      </div>
                      
                      <textarea
                        placeholder="Extraction prompt (e.g., Extract the BT-RADS assessment from this radiology report...)"
                        value={datapoint.prompt}
                        onChange={(e) => updateDatapoint(index, 'prompt', e.target.value)}
                        rows={3}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      
                      <div className="flex items-center space-x-4">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={datapoint.use_rag}
                            onChange={(e) => updateDatapoint(index, 'use_rag', e.target.checked)}
                            className="mr-2"
                          />
                          <span className="text-sm">Use RAG</span>
                        </label>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm">Confidence:</span>
                          <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.1"
                            value={datapoint.confidence_threshold}
                            onChange={(e) => updateDatapoint(index, 'confidence_threshold', parseFloat(e.target.value))}
                            className="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  <Button onClick={addDatapoint} variant="outline" className="w-full">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Another Datapoint
                  </Button>
                </CardContent>
              </Card>

              {/* LLM Configuration */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Brain className="h-5 w-5 mr-2" />
                    LLM Configuration
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Model
                    </label>
                    <select
                      value={llmConfig.model_name}
                      onChange={(e) => setLlmConfig({...llmConfig, model_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      disabled={modelsLoading}
                    >
                      <option value="">
                        {modelsLoading ? "Loading models..." : "Select model..."}
                      </option>
                      {(modelsData?.available_models || []).map(modelName => (
                        <option key={modelName} value={modelName}>
                          {modelName}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Temperature</label>
                      <input
                        type="number"
                        min="0"
                        max="2"
                        step="0.1"
                        value={llmConfig.temperature}
                        onChange={(e) => setLlmConfig({...llmConfig, temperature: parseFloat(e.target.value)})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Max Tokens</label>
                      <input
                        type="number"
                        min="1"
                        max="4096"
                        value={llmConfig.max_tokens}
                        onChange={(e) => setLlmConfig({...llmConfig, max_tokens: parseInt(e.target.value)})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Timeout (s)</label>
                      <input
                        type="number"
                        min="10"
                        max="300"
                        value={llmConfig.timeout}
                        onChange={(e) => setLlmConfig({...llmConfig, timeout: parseInt(e.target.value)})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="flex justify-between">
                <Button variant="outline" onClick={() => setStep(1)}>
                  Back
                </Button>
                <Button onClick={() => setStep(3)} className="medical-gradient">
                  Review Configuration
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Review */}
          {step === 3 && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Job Summary</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Job Name:</span> {jobName}
                    </div>
                    <div>
                      <span className="font-medium">Data File:</span> {file?.name}
                    </div>
                    <div>
                      <span className="font-medium">Text Column:</span> {textColumn}
                    </div>
                    <div>
                      <span className="font-medium">Ground Truth:</span> {groundTruthColumn || "None"}
                    </div>
                    <div>
                      <span className="font-medium">Datapoints:</span> {(datapoints || []).length}
                    </div>
                    <div>
                      <span className="font-medium">Model:</span> {llmConfig.model_name || "Default"}
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-medium mb-2">Datapoints to Extract:</h4>
                    <div className="space-y-2">
                      {(datapoints || []).map((dp, index) => (
                        <div key={index} className="flex items-center space-x-2">
                          <Badge variant="outline">{dp.name}</Badge>
                          <span className="text-sm text-gray-500">({dp.extraction_strategy})</span>
                          {dp.use_rag && <Badge variant="info">RAG</Badge>}
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="flex justify-between">
                <Button variant="outline" onClick={() => setStep(2)}>
                  Back
                </Button>
                <Button 
                  onClick={handleSubmit} 
                  disabled={processing}
                  className="medical-gradient"
                >
                  {processing ? "Creating Job..." : "Create Job"}
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}