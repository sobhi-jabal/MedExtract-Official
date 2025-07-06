"use client";

import { useState, useCallback, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { 
  Upload, 
  FileText, 
  Settings, 
  Play, 
  Download, 
  AlertCircle, 
  CheckCircle, 
  Loader2,
  Plus,
  X,
  ChevronDown,
  ChevronUp,
  Info,
  Save,
  FolderOpen,
  StopCircle
} from "lucide-react";

// UI Components
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Slider } from "@/components/ui/slider";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

// API
import { 
  healthAPI, 
  modelsAPI, 
  extractionAPI,
  createProgressWebSocket,
  downloadFile,
  type HealthStatus,
  type FilePreview,
  type DatapointConfig,
  type ExtractionProgress,
  type ExtractionConfig
} from "@/lib/api_simplified";

interface FewShotExample {
  report: string;
  extracted: string;
  type: 'simple' | 'detailed' | 'negative';
}

interface ExtendedDatapointConfig extends DatapointConfig {
  systemPrompt?: string;
  examples?: FewShotExample[];
  enableRAG?: boolean;
  temperature?: number;
  topK?: number;
  topP?: number;
}

export default function MedExtractUI() {
  const queryClient = useQueryClient();
  
  // File upload state
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<FilePreview | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFilePath, setUploadedFilePath] = useState<string>("");
  
  // Configuration state
  const [textColumn, setTextColumn] = useState<string>("");
  const [groundTruthColumn, setGroundTruthColumn] = useState<string>("");
  
  // Main extraction configuration
  const [datapoint, setDatapoint] = useState<ExtendedDatapointConfig>({
    name: "",
    instruction: "",
    query: "",
    default_value: "NR",
    valid_values: [],
    few_shots: [],
    systemPrompt: "",
    examples: [],
    enableRAG: true,
    temperature: 0.1,
    topK: 40,
    topP: 0.9
  });
  
  // LLM settings
  const [llmModel, setLlmModel] = useState("");
  const [customModelName, setCustomModelName] = useState("");
  const [isPullingModel, setIsPullingModel] = useState(false);
  const [globalRAG, setGlobalRAG] = useState(false);
  const [temperature, setTemperature] = useState(0.1);
  const [topK, setTopK] = useState(40);
  const [topP, setTopP] = useState(0.9);
  const [useFewShots, setUseFewShots] = useState(false);
  
  // RAG Advanced settings
  const [chunkSize, setChunkSize] = useState(800);
  const [chunkOverlap, setChunkOverlap] = useState(150);
  const [retrieverType, setRetrieverType] = useState("hybrid");
  const [useReranker, setUseReranker] = useState(false);
  const [rerankerTopN, setRerankerTopN] = useState(3);
  const [numCtx, setNumCtx] = useState(4096);
  
  // Processing configuration
  const [saveFrequency, setSaveFrequency] = useState(10);
  const [enableCheckpoints, setEnableCheckpoints] = useState(false);
  const [outputDirectory, setOutputDirectory] = useState("./output");
  
  // Extraction state
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionProgress, setExtractionProgress] = useState<ExtractionProgress | null>(null);
  const [extractionResults, setExtractionResults] = useState<any>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  // UI state
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [activeExampleTab, setActiveExampleTab] = useState<'simple' | 'detailed' | 'negative'>('simple');
  const [validResponsesText, setValidResponsesText] = useState("");

  // Queries
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: healthAPI.check,
    refetchInterval: 30000,
  });

  const { data: modelsData } = useQuery({
    queryKey: ['models'],
    queryFn: modelsAPI.list
  });

  // File upload handler
  const handleFileUpload = useCallback(async (file: File) => {
    setUploadedFile(file);
    // Store the full path if available (note: browsers restrict full path access for security)
    // @ts-ignore - webkitRelativePath is a non-standard property
    const path = file.webkitRelativePath || file.name;
    setUploadedFilePath(path);
    
    try {
      const preview = await extractionAPI.preview(file);
      setFilePreview(preview);
      
      // Auto-detect text column
      const columns = preview.columns;
      const textColumnCandidates = [
        'text', 'report', 'report_text', 'Report Text', 'content', 
        'document', 'clinical_note', 'note', 'narrative'
      ];
      const detectedColumn = columns.find((col: string) => 
        textColumnCandidates.some(candidate => 
          col.toLowerCase().includes(candidate.toLowerCase())
        )
      ) || columns[0];
      setTextColumn(detectedColumn);
      
      // Auto-detect ground truth column
      const gtCandidates = [
        'ground_truth', 'label', 'target', 'expected', 'actual',
        'score', 'assessment', 'result'
      ];
      const detectedGT = columns.find((col: string) =>
        gtCandidates.some(candidate =>
          col.toLowerCase().includes(candidate.toLowerCase())
        )
      );
      if (detectedGT) {
        setGroundTruthColumn(detectedGT);
      }
    } catch (error: any) {
      console.error("File preview error:", error);
      console.error("Error details:", {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        statusText: error.response?.statusText,
      });
      
      let errorMessage = "Failed to preview file. ";
      if (error.response?.status === 400) {
        errorMessage += error.response.data?.detail || "Please check the file format.";
      } else if (error.response?.status === 0 || error.code === 'ERR_NETWORK') {
        errorMessage += "Cannot connect to backend. Please check if the backend is running.";
      } else {
        errorMessage += error.message || "Please check the file format.";
      }
      
      alert(errorMessage);
    }
  }, []);

  // Load preset - commented out as presetsAPI is not implemented yet
  // const loadPreset = async (presetId: string) => {
  //   if (!presetId || presetId === '_custom') return;
    
  //   try {
  //     const preset = await presetsAPI.get(presetId);
  //     setSelectedPreset(presetId);
      
  //     // Load first datapoint from preset
  //     if (preset.datapoint_configs && preset.datapoint_configs.length > 0) {
  //       const firstConfig = preset.datapoint_configs[0];
  //       setDatapoint({
  //         ...datapoint,
  //         name: firstConfig.name,
  //         instruction: firstConfig.instruction,
  //         query: firstConfig.query || "",
  //         default_value: firstConfig.default_value || "NR",
  //         valid_values: firstConfig.valid_values || [],
  //         few_shots: firstConfig.few_shots || []
  //       });
  //     }
      
  //     // Apply default settings
  //     if (preset.default_settings) {
  //       setGlobalRAG(preset.default_settings.use_rag ?? true);
  //       setTemperature(preset.default_settings.temperature ?? 0.1);
  //       setTopK(preset.default_settings.top_k ?? 40);
  //       setTopP(preset.default_settings.top_p ?? 0.9);
  //     }
  //   } catch (error) {
  //     console.error("Error loading preset:", error);
  //   }
  // };

  // Update valid responses from text
  useEffect(() => {
    if (validResponsesText) {
      // Split by comma or semicolon
      const values = validResponsesText
        .split(/[,;]/)
        .map(v => v.trim())
        .filter(v => v.length > 0);
      setDatapoint(prev => ({ ...prev, valid_values: values }));
    } else {
      setDatapoint(prev => ({ ...prev, valid_values: [] }));
    }
  }, [validResponsesText]);

  // Add few-shot example
  const addExample = (type: 'simple' | 'detailed' | 'negative') => {
    const newExample: FewShotExample = {
      report: "",
      extracted: "",
      type
    };
    
    setDatapoint(prev => ({
      ...prev,
      examples: [...(prev.examples || []), newExample]
    }));
  };

  // Update example
  const updateExample = (index: number, field: 'report' | 'extracted', value: string) => {
    setDatapoint(prev => ({
      ...prev,
      examples: (prev.examples || []).map((ex, i) => 
        i === index ? { ...ex, [field]: value } : ex
      )
    }));
  };

  // Remove example
  const removeExample = (index: number) => {
    setDatapoint(prev => ({
      ...prev,
      examples: (prev.examples || []).filter((_, i) => i !== index)
    }));
  };

  // Convert examples to few_shots format
  const convertExamplesToFewShots = (examples: FewShotExample[]): any[] => {
    return examples.flatMap(ex => [
      { role: "user", content: ex.report },
      { role: "assistant", content: ex.extracted }
    ]);
  };

  // Pull model function
  const pullModel = async () => {
    if (!customModelName.trim()) {
      alert("Please enter a model name");
      return;
    }

    setIsPullingModel(true);
    try {
      // Show pulling message
      alert(`Pulling model ${customModelName.trim()}...\nThis may take several minutes depending on the model size.\nCheck the backend logs for progress.`);
      
      const result = await modelsAPI.pull(customModelName.trim());
      if (result.status === "success") {
        alert(`Model ${result.model_name} pulled successfully!`);
        setCustomModelName("");
        // Refetch models list
        await queryClient.invalidateQueries({ queryKey: ['models'] });
        // Set the newly pulled model as selected
        setLlmModel(result.model_name);
      }
    } catch (error: any) {
      console.error("Pull error:", error);
      alert(`Failed to pull model: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsPullingModel(false);
    }
  };

  // Delete model function
  const deleteModel = async (modelName: string) => {
    if (!confirm(`Are you sure you want to delete the model "${modelName}"?\nThis cannot be undone.`)) {
      return;
    }

    try {
      const result = await modelsAPI.delete(modelName);
      if (result.status === "success") {
        alert(`Model ${result.model_name} deleted successfully!`);
        // Refetch models list
        await queryClient.invalidateQueries({ queryKey: ['models'] });
        // If deleted model was selected, reset to first available
        if (llmModel === modelName) {
          const models = modelsData?.available_models || [];
          setLlmModel(models[0] || "phi4:latest");
        }
      }
    } catch (error: any) {
      console.error("Delete error:", error);
      alert(`Failed to delete model: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Stop extraction
  const stopExtraction = async () => {
    if (sessionId && isExtracting) {
      try {
        // Save current progress before stopping
        saveConfiguration();
        
        // Call API to stop extraction
        await extractionAPI.stop(sessionId);
        
        setIsExtracting(false);
        alert(`Extraction stopped at row ${extractionProgress?.current_row || 0}. Configuration with progress has been saved.`);
      } catch (error) {
        console.error("Error stopping extraction:", error);
      }
    }
  };

  // Start extraction
  const startExtraction = async () => {
    if (!uploadedFile || !textColumn || !datapoint.name || !datapoint.instruction || !llmModel) {
      alert("Please complete all required fields:\n- Upload a file\n- Select text column\n- Enter datapoint name\n- Enter extraction instruction\n- Select an LLM model");
      return;
    }

    setIsExtracting(true);
    setExtractionProgress(null);
    setExtractionResults(null);

    const config: ExtractionConfig = {
      text_column: textColumn,
      ground_truth_column: (groundTruthColumn && groundTruthColumn !== '_none') ? groundTruthColumn : undefined,
      datapoint_configs: [{
        name: datapoint.name,
        instruction: datapoint.instruction,
        query: datapoint.query,
        default_value: datapoint.default_value,
        valid_values: datapoint.valid_values,
        few_shots: useFewShots ? convertExamplesToFewShots(datapoint.examples || []) : []
      }],
      llm_model: llmModel,
      use_rag: globalRAG && (datapoint.enableRAG ?? true),
      temperature: temperature,
      top_k: topK,
      top_p: topP,
      num_ctx: numCtx,
      extraction_strategy: "single_call",
      batch_size: 5,
      chunk_size: chunkSize,
      chunk_overlap: chunkOverlap,
      retriever_type: retrieverType,
      reranker_top_n: rerankerTopN,
      use_few_shots: useFewShots,
      save_intermediate: enableCheckpoints,
      save_frequency: saveFrequency,
      store_metadata: true,
      output_directory: outputDirectory
    };

    try {
      const result = await extractionAPI.start(uploadedFile, config);
      const { session_id } = result;
      setSessionId(session_id);

      // Use WebSocket for real-time progress
      const ws = createProgressWebSocket(session_id, (data) => {
        setExtractionProgress(data);
        
        if (data.status === 'completed') {
          ws.close();
          extractionAPI.getResults(session_id).then(results => {
            setExtractionResults(results);
            setIsExtracting(false);
          });
        } else if (data.status === 'failed') {
          ws.close();
          setIsExtracting(false);
          alert(`Extraction failed: ${data.error}`);
        }
      });

      // Fallback to polling (also start polling immediately as backup)
      const progressInterval = setInterval(async () => {
        try {
          const progress = await extractionAPI.getProgress(session_id);
          setExtractionProgress(progress);

          if (progress.status === 'completed' || progress.status === 'failed' || progress.status === 'stopped') {
            clearInterval(progressInterval);
            if (progress.status === 'completed') {
              const results = await extractionAPI.getResults(session_id);
              setExtractionResults(results);
            }
            setIsExtracting(false);
            if (progress.status === 'stopped') {
              alert(`Extraction stopped at row ${progress.current_row}. Configuration saved.`);
            }
          }
        } catch (error) {
          console.error("Progress polling error:", error);
        }
      }, 500); // Poll every 500ms for more responsive updates

      // Handle WebSocket errors
      ws.onerror = (error) => {
        console.log("WebSocket error, using polling fallback:", error);
      };
      
      // Clean up polling when WebSocket works
      ws.onopen = () => {
        console.log("WebSocket connected for progress updates");
      };

    } catch (error: any) {
      setIsExtracting(false);
      console.error("Extraction error:", error);
      const errorMessage = error.response?.data?.detail || error.message || "Failed to start extraction";
      alert(`Extraction failed: ${errorMessage}`);
    }
  };

  // Download results
  const downloadResults = async (format: 'csv' | 'excel') => {
    if (!sessionId) return;

    try {
      const blob = await extractionAPI.download(sessionId, format);
      const timestamp = new Date().toISOString().replace(/[-:]/g, '').replace('T', '_').split('.')[0];
      const filename = `${datapoint.name}_extraction_${timestamp}.${format === 'csv' ? 'csv' : 'xlsx'}`;
      downloadFile(blob, filename);
    } catch (error) {
      console.error("Download error:", error);
      alert("Failed to download results");
    }
  };

  // Save configuration
  const saveConfiguration = () => {
    const config = {
      version: "1.0",
      timestamp: new Date().toISOString(),
      sourceFile: {
        filename: uploadedFile?.name || null,
        filepath: uploadedFilePath || uploadedFile?.name || null, // Full path when available
        totalRows: filePreview?.total_rows || null,
        columns: filePreview?.columns || []
      },
      extractionTask: {
        textColumn,
        groundTruthColumn,
        datapoint: {
          name: datapoint.name,
          instruction: datapoint.instruction,
          default_value: datapoint.default_value,
          valid_values: datapoint.valid_values,
          examples: datapoint.examples
        }
      },
      modelConfig: {
        llmModel,
        temperature,
        topK,
        topP,
        numCtx
      },
      ragConfig: {
        enabled: globalRAG,
        query: datapoint.query, // Move query to RAG config where it belongs
        chunkSize,
        chunkOverlap,
        retrieverType,
        useReranker: globalRAG && useReranker,
        rerankerTopN
      },
      executionConfig: {
        useFewShots,
        enableCheckpoints,
        saveFrequency,
        outputDirectory,
        lastProcessedRow: extractionProgress?.current_row || 0
      }
    };

    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const timestamp = new Date().toISOString().replace(/[-:]/g, '').replace('T', '_').split('.')[0];
    const filename = `medextract_config_${timestamp}.json`;
    downloadFile(blob, filename);
  };

  // Load configuration
  const loadConfiguration = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const config = JSON.parse(e.target?.result as string);
        
        // Handle both old and new config formats
        if (!config.settings && !config.extractionTask) {
          alert("Invalid configuration file format");
          return;
        }
        
        // Show source file info if available
        if (config.sourceFile) {
          const filepath = config.sourceFile.filepath || config.sourceFile.filename || 'Unknown';
          alert(`Configuration loaded successfully!\n\nSource file: ${filepath}\nTotal rows: ${config.sourceFile.totalRows || 'Unknown'}\n\nPlease upload the corresponding data file to continue.`);
        }

        // Handle new format
        if (config.extractionTask) {
          // Load extraction task settings
          setTextColumn(config.extractionTask.textColumn || "");
          setGroundTruthColumn(config.extractionTask.groundTruthColumn || "");
          
          if (config.extractionTask.datapoint) {
            const dp = config.extractionTask.datapoint;
            setDatapoint({
              ...datapoint,
              name: dp.name || "",
              instruction: dp.instruction || "",
              query: config.ragConfig?.query || "", // Get query from RAG config
              default_value: dp.default_value || "NR",
              valid_values: dp.valid_values || [],
              examples: dp.examples || []
            });
            
            // Update valid responses text
            if (dp.valid_values?.length > 0) {
              setValidResponsesText(dp.valid_values.join(", "));
            }
          }
          
          // Load model config
          if (config.modelConfig) {
            setLlmModel(config.modelConfig.llmModel || "");
            setTemperature(config.modelConfig.temperature ?? 0.1);
            setTopK(config.modelConfig.topK ?? 40);
            setTopP(config.modelConfig.topP ?? 0.9);
            setNumCtx(config.modelConfig.numCtx ?? 4096);
          }
          
          // Load RAG config
          if (config.ragConfig) {
            setGlobalRAG(config.ragConfig.enabled ?? false);
            setChunkSize(config.ragConfig.chunkSize ?? 800);
            setChunkOverlap(config.ragConfig.chunkOverlap ?? 150);
            setRetrieverType(config.ragConfig.retrieverType || "hybrid");
            setUseReranker(config.ragConfig.useReranker ?? false);
            setRerankerTopN(config.ragConfig.rerankerTopN ?? 3);
          }
          
          // Load execution config
          if (config.executionConfig) {
            setUseFewShots(config.executionConfig.useFewShots ?? false);
            setEnableCheckpoints(config.executionConfig.enableCheckpoints ?? false);
            setSaveFrequency(config.executionConfig.saveFrequency ?? 10);
            setOutputDirectory(config.executionConfig.outputDirectory || "./output");
          }
        } else {
          // Handle old format (backwards compatibility)
          const settings = config.settings;
          
          setTextColumn(settings.textColumn || "");
          setGroundTruthColumn(settings.groundTruthColumn || "");
          
          if (settings.datapoint) {
            setDatapoint({
              ...datapoint,
              name: settings.datapoint.name || "",
              instruction: settings.datapoint.instruction || "",
              query: settings.datapoint.query || "",
              default_value: settings.datapoint.default_value || "NR",
              valid_values: settings.datapoint.valid_values || [],
              examples: settings.datapoint.examples || []
            });
            
            if (settings.datapoint.valid_values?.length > 0) {
              setValidResponsesText(settings.datapoint.valid_values.join(", "));
            }
          }
          
          setLlmModel(settings.llmModel || "");
          setTemperature(settings.temperature ?? 0.1);
          setTopK(settings.topK ?? 40);
          setTopP(settings.topP ?? 0.9);
          setNumCtx(settings.numCtx ?? 4096);
          setGlobalRAG(settings.globalRAG ?? false);
          setChunkSize(settings.chunkSize ?? 800);
          setChunkOverlap(settings.chunkOverlap ?? 150);
          setRetrieverType(settings.retrieverType || "hybrid");
          setUseReranker(settings.useReranker ?? false);
          setRerankerTopN(settings.rerankerTopN ?? 3);
          setUseFewShots(settings.useFewShots ?? false);
          setEnableCheckpoints(settings.enableCheckpoints ?? false);
          setSaveFrequency(settings.saveFrequency ?? 10);
          setOutputDirectory(settings.outputDirectory || "./output");
        }
        
        alert("Configuration loaded successfully!");
      } catch (error) {
        console.error("Error loading configuration:", error);
        alert("Failed to load configuration file. Please check the file format.");
      }
    };
    
    reader.readAsText(file);
    
    // Reset the input so the same file can be loaded again
    event.target.value = '';
  };

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-bold text-blue-600">MedExtract</span>
                  <h1 className="text-2xl font-semibold text-gray-600">Medical Report Data Processing and Extraction</h1>
                </div>
                <p className="text-sm text-gray-500 mt-1">Configure and run your extraction process</p>
              </div>
              <div className="flex items-center space-x-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={saveConfiguration}
                  title="Save configuration"
                >
                  <Save className="h-4 w-4 mr-2" />
                  Save Config
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => document.getElementById('config-upload')?.click()}
                  title="Load configuration"
                >
                  <FolderOpen className="h-4 w-4 mr-2" />
                  Load Config
                </Button>
                <input
                  id="config-upload"
                  type="file"
                  accept=".json"
                  style={{ display: 'none' }}
                  onChange={loadConfiguration}
                />
                <Badge 
                  variant={health?.status === 'healthy' ? 'default' : 'destructive'}
                  className={health?.status === 'healthy' ? 'bg-green-500 hover:bg-green-600' : ''}
                >
                  {health?.status || 'checking...'}
                </Badge>
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
          {/* Required Fields Notice */}
          <Alert className="border-blue-200 bg-blue-50/50">
            <Info className="h-4 w-4" />
            <AlertDescription>
              Fields marked with <span className="text-red-500">*</span> are required. All other fields are optional.
            </AlertDescription>
          </Alert>

          {/* File Upload Section */}
          <Card>
            <CardHeader>
              <CardTitle>Data Source</CardTitle>
              <CardDescription>Upload your data file and select the appropriate columns</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <div
                    className={`
                      border-2 border-dashed rounded-lg p-8 text-center transition-all
                      ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
                      ${uploadedFile ? 'bg-gray-50' : 'bg-white'}
                    `}
                    onDrop={(e) => {
                      e.preventDefault();
                      setIsDragging(false);
                      const file = e.dataTransfer.files[0];
                      if (file) handleFileUpload(file);
                    }}
                    onDragOver={(e) => {
                      e.preventDefault();
                      setIsDragging(true);
                    }}
                    onDragLeave={() => setIsDragging(false)}
                  >
                    {uploadedFile ? (
                      <div>
                        <FileText className="h-12 w-12 mx-auto text-blue-600 mb-2" />
                        <p className="font-medium text-gray-900">{uploadedFile.name}</p>
                        <p className="text-sm text-gray-500 mt-1">
                          {filePreview ? `${filePreview.total_rows} rows, ${filePreview.columns.length} columns` : 'Processing...'}
                        </p>
                        <Button
                          variant="outline"
                          size="sm"
                          className="mt-3"
                          onClick={() => {
                            const input = document.createElement('input');
                            input.type = 'file';
                            input.accept = '.csv,.xlsx,.xls';
                            input.onchange = (e) => {
                              const file = (e.target as HTMLInputElement).files?.[0];
                              if (file) handleFileUpload(file);
                            };
                            input.click();
                          }}
                          disabled={isExtracting}
                        >
                          Change File
                        </Button>
                      </div>
                    ) : (
                      <div>
                        <Upload className="h-12 w-12 mx-auto text-gray-400 mb-2" />
                        <p className="text-gray-600 mb-2">Drop your CSV or Excel file here</p>
                        <Button
                          variant="outline"
                          onClick={() => {
                            const input = document.createElement('input');
                            input.type = 'file';
                            input.accept = '.csv,.xlsx,.xls';
                            input.onchange = (e) => {
                              const file = (e.target as HTMLInputElement).files?.[0];
                              if (file) handleFileUpload(file);
                            };
                            input.click();
                          }}
                          disabled={isExtracting}
                        >
                          Select File
                        </Button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <Label htmlFor="text-column">
                      Text Column
                      <span className="text-red-500 ml-1">*</span>
                    </Label>
                    <Select value={textColumn} onValueChange={setTextColumn} disabled={isExtracting}>
                      <SelectTrigger id="text-column" disabled={isExtracting}>
                        <SelectValue placeholder="Select the column containing medical reports" />
                      </SelectTrigger>
                      <SelectContent>
                        {filePreview?.columns.map(col => (
                          <SelectItem key={col} value={col}>{col}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="gt-column">Ground Truth Column (Optional)</Label>
                    <Select value={groundTruthColumn} onValueChange={setGroundTruthColumn} disabled={isExtracting}>
                      <SelectTrigger id="gt-column" disabled={isExtracting}>
                        <SelectValue placeholder="Select ground truth column for evaluation" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="_none">None</SelectItem>
                        {filePreview?.columns.map(col => (
                          <SelectItem key={col} value={col}>{col}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Extraction Task */}
          <Card>
            <CardHeader>
              <CardTitle>Extraction Task</CardTitle>
              <CardDescription>Define what information you want to extract from the medical reports</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Datapoint Configuration */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="datapoint-name">
                      Datapoint to Extract
                      <span className="text-red-500 ml-1">*</span>
                    </Label>
                    <Input
                      id="datapoint-name"
                      placeholder="e.g., diagnosis, medication_status, assessment"
                      value={datapoint.name}
                      onChange={(e) => setDatapoint(prev => ({ ...prev, name: e.target.value }))}
                      disabled={isExtracting}
                    />
                  </div>

                  <div>
                    <Label htmlFor="instruction">
                      Extraction Instruction
                      <span className="text-red-500 ml-1">*</span>
                    </Label>
                    <Textarea
                      id="instruction"
                      placeholder="Describe precisely what to extract from the medical reports..."
                      rows={4}
                      value={datapoint.instruction}
                      onChange={(e) => setDatapoint(prev => ({ ...prev, instruction: e.target.value }))}
                      disabled={isExtracting}
                    />
                  </div>

                </div>

                <div className="space-y-4">
                  <div>
                    <Label htmlFor="default-value">
                      Default Value
                      <span className="text-muted-foreground text-sm ml-1">(optional)</span>
                    </Label>
                    <Input
                      id="default-value"
                      placeholder="NR"
                      value={datapoint.default_value}
                      onChange={(e) => setDatapoint(prev => ({ ...prev, default_value: e.target.value }))}
                      disabled={isExtracting}
                    />
                  </div>

                  <div>
                    <Label htmlFor="valid-responses">
                      Valid Responses
                      <span className="text-muted-foreground text-sm ml-1">(optional)</span>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Info className="h-3 w-3 inline ml-1" />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Comma or semicolon separated list. Leave empty to accept any value</p>
                        </TooltipContent>
                      </Tooltip>
                    </Label>
                    <Textarea
                      id="valid-responses"
                      placeholder="e.g., Yes, No, Unknown; or BT-RADS 0; BT-RADS 1; BT-RADS 2"
                      rows={4}
                      value={validResponsesText}
                      onChange={(e) => setValidResponsesText(e.target.value)}
                      disabled={isExtracting}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Model Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Model Configuration</CardTitle>
              <CardDescription>Configure the language model parameters</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="llm-model">
                      LLM Model
                      <span className="text-red-500 ml-1">*</span>
                    </Label>
                    <div className="flex gap-2">
                      <Select value={llmModel} onValueChange={setLlmModel} disabled={isExtracting}>
                        <SelectTrigger id="llm-model" className="flex-1" disabled={isExtracting}>
                          <SelectValue placeholder="Select a model..." />
                        </SelectTrigger>
                        <SelectContent>
                          {modelsData?.available_models?.map((model: string) => (
                            <SelectItem key={model} value={model}>{model}</SelectItem>
                          ))}
                          {customModelName && !modelsData?.available_models?.includes(customModelName) && (
                            <SelectItem value={customModelName}>{customModelName} (custom)</SelectItem>
                          )}
                        </SelectContent>
                      </Select>
                      <Button
                        onClick={() => deleteModel(llmModel)}
                        variant="destructive"
                        size="icon"
                        title="Delete selected model"
                        disabled={!llmModel || modelsData?.available_models?.length === 1 || isExtracting}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                    
                    <div className="flex gap-2 mt-2">
                      <Input
                        placeholder="Enter custom model name (e.g., phi4:14b)"
                        value={customModelName}
                        onChange={(e) => {
                          setCustomModelName(e.target.value);
                          // Auto-select custom model if it's typed
                          if (e.target.value.trim()) {
                            setLlmModel(e.target.value.trim());
                          }
                        }}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter' && !isPullingModel) {
                            pullModel();
                          }
                        }}
                        disabled={isExtracting}
                      />
                      <Button
                        onClick={pullModel}
                        disabled={isPullingModel || !customModelName.trim() || isExtracting}
                        size="sm"
                      >
                        {isPullingModel ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Pulling...
                          </>
                        ) : (
                          'Pull Model'
                        )}
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Pull models from Ollama registry or use a custom model name
                    </p>
                  </div>


                </div>

                <div className="space-y-4">
                  <div>
                    <Label htmlFor="temperature">
                      Temperature: {temperature.toFixed(1)}
                    </Label>
                    <Slider
                      id="temperature"
                      min={0}
                      max={1}
                      step={0.1}
                      value={[temperature]}
                      onValueChange={([v]) => setTemperature(v)}
                      disabled={isExtracting}
                    />
                  </div>

                  <div>
                    <Label htmlFor="top-k">Top K: {topK}</Label>
                    <Slider
                      id="top-k"
                      min={1}
                      max={100}
                      step={1}
                      value={[topK]}
                      onValueChange={([v]) => setTopK(v)}
                      disabled={isExtracting}
                    />
                  </div>

                  <div>
                    <Label htmlFor="top-p">Top P: {topP.toFixed(1)}</Label>
                    <Slider
                      id="top-p"
                      min={0}
                      max={1}
                      step={0.1}
                      value={[topP]}
                      onValueChange={([v]) => setTopP(v)}
                      disabled={isExtracting}
                    />
                  </div>

                  <div>
                    <Label htmlFor="num-ctx">
                      Context Window (tokens)
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Info className="h-3 w-3 inline ml-1" />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Maximum context length. Common values: 4096, 8192, 16384, 32768, 128000</p>
                        </TooltipContent>
                      </Tooltip>
                    </Label>
                    <Input
                      id="num-ctx"
                      type="number"
                      min="2048"
                      max="200000"
                      step="1024"
                      value={numCtx}
                      onChange={(e) => {
                        const value = e.target.value;
                        if (value === '') {
                          setNumCtx(0); // Allow empty field temporarily
                        } else {
                          const num = parseInt(value);
                          if (!isNaN(num) && num >= 0) {
                            setNumCtx(num);
                          }
                        }
                      }}
                      onBlur={(e) => {
                        // On blur, if empty or too small, set to minimum
                        if (!e.target.value || parseInt(e.target.value) < 2048) {
                          setNumCtx(4096);
                        }
                      }}
                      disabled={isExtracting}
                      className="mt-2"
                    />
                  </div>
                </div>
              </div>

            </CardContent>
          </Card>

          {/* RAG Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>RAG Configuration</CardTitle>
              <CardDescription>Configure Retrieval-Augmented Generation settings for better context understanding</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="enable-rag">Enable RAG</Label>
                  <p className="text-sm text-muted-foreground">Use retrieval to provide relevant context to the model</p>
                </div>
                <Switch
                  id="enable-rag"
                  checked={globalRAG}
                  onCheckedChange={setGlobalRAG}
                  disabled={isExtracting}
                />
              </div>

              {globalRAG && (
                <>
                  <Separator />
                  
                  <div>
                    <Label htmlFor="rag-query">
                      RAG Search Query
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Info className="h-3 w-3 inline ml-1" />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Keywords to help find relevant sections in the medical reports</p>
                        </TooltipContent>
                      </Tooltip>
                    </Label>
                    <Input
                      id="rag-query"
                      placeholder="e.g., diagnosis disease condition findings assessment"
                      value={datapoint.query}
                      onChange={(e) => setDatapoint(prev => ({ ...prev, query: e.target.value }))}
                      className="mt-2"
                      disabled={isExtracting}
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <Label htmlFor="retriever">Retrieval Strategy</Label>
                      <Select value={retrieverType} onValueChange={setRetrieverType} disabled={isExtracting}>
                        <SelectTrigger id="retriever" className="mt-2" disabled={isExtracting}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="semantic">Semantic Search</SelectItem>
                          <SelectItem value="keyword">Keyword Search (BM25)</SelectItem>
                          <SelectItem value="hybrid">Hybrid (Semantic + Keyword)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <div className="space-y-1">
                          <Label htmlFor="reranker">Use Reranker</Label>
                          <p className="text-sm text-muted-foreground">Improve result relevance</p>
                        </div>
                        <Switch
                          id="reranker"
                          checked={useReranker}
                          onCheckedChange={setUseReranker}
                          disabled={isExtracting}
                        />
                      </div>
                      {useReranker && (
                        <div className="mt-3">
                          <Label htmlFor="reranker-topn">Reranker Top N: {rerankerTopN}</Label>
                          <Slider
                            id="reranker-topn"
                            min={1}
                            max={10}
                            step={1}
                            value={[rerankerTopN]}
                            onValueChange={([v]) => setRerankerTopN(v)}
                            disabled={isExtracting}
                            className="mt-2"
                          />
                          <p className="text-xs text-muted-foreground mt-1">Number of results after reranking</p>
                        </div>
                      )}
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-sm font-medium">Advanced Settings</h4>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowAdvanced(!showAdvanced)}
                        disabled={isExtracting}
                      >
                        {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </Button>
                    </div>
                    
                    {showAdvanced && (
                      <div className="space-y-4 p-4 border rounded-lg bg-muted/50">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="chunk-size">Chunk Size: {chunkSize}</Label>
                            <Slider
                              id="chunk-size"
                              min={100}
                              max={2000}
                              step={50}
                              value={[chunkSize]}
                              onValueChange={([v]) => setChunkSize(v)}
                              className="mt-2"
                              disabled={isExtracting}
                            />
                            <p className="text-xs text-muted-foreground mt-1">Size of text chunks for retrieval</p>
                          </div>
                          
                          <div>
                            <Label htmlFor="chunk-overlap">Chunk Overlap: {chunkOverlap}</Label>
                            <Slider
                              id="chunk-overlap"
                              min={0}
                              max={500}
                              step={25}
                              value={[chunkOverlap]}
                              onValueChange={([v]) => setChunkOverlap(v)}
                              disabled={isExtracting}
                              className="mt-2"
                            />
                            <p className="text-xs text-muted-foreground mt-1">Overlap between consecutive chunks</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Few-shot Prompting */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Few-shot Prompting</CardTitle>
                  <CardDescription>Provide examples of input reports and their expected extractions to guide the model</CardDescription>
                </div>
                <Switch
                  id="use-fewshots"
                  checked={useFewShots}
                  onCheckedChange={setUseFewShots}
                  disabled={isExtracting}
                />
              </div>
            </CardHeader>
              <CardContent>
                {useFewShots ? (
                  <Tabs value={activeExampleTab} onValueChange={(v) => setActiveExampleTab(v as any)}>
                    <TabsList>
                      <TabsTrigger value="simple">Simple Examples</TabsTrigger>
                      <TabsTrigger value="detailed">Detailed Examples</TabsTrigger>
                      <TabsTrigger value="negative">Negative Examples</TabsTrigger>
                    </TabsList>

                  <TabsContent value={activeExampleTab} className="mt-4">
                    <div className="space-y-4">
                      {(datapoint.examples || [])
                        .filter(ex => ex.type === activeExampleTab)
                        .map((example, index) => (
                          <Card key={index}>
                            <CardContent className="pt-4">
                              <div className="flex justify-end mb-2">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {
                                    const globalIndex = (datapoint.examples || []).indexOf(example);
                                    removeExample(globalIndex);
                                  }}
                                >
                                  <X className="h-4 w-4" />
                                </Button>
                              </div>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                  <Label>
                                    Example Input
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <Info className="h-3 w-3 inline ml-1" />
                                      </TooltipTrigger>
                                      <TooltipContent>
                                        <p>A sample medical report text that contains the information to extract</p>
                                      </TooltipContent>
                                    </Tooltip>
                                  </Label>
                                  <Textarea
                                    placeholder="Example: 'The patient presents with...'"  
                                    rows={3}
                                    value={example.report}
                                    onChange={(e) => {
                                      const globalIndex = (datapoint.examples || []).indexOf(example);
                                      updateExample(globalIndex, 'report', e.target.value);
                                    }}
                                    className="mt-2"
                                  />
                                </div>
                                <div>
                                  <Label>
                                    Expected Output
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <Info className="h-3 w-3 inline ml-1" />
                                      </TooltipTrigger>
                                      <TooltipContent>
                                        <p>The exact value you expect to extract from this example (not a JSON object)</p>
                                      </TooltipContent>
                                    </Tooltip>
                                  </Label>
                                  <Textarea
                                    placeholder="Example: 'BT-RADS 2' or 'Positive' or 'No evidence of disease'"
                                    rows={3}
                                    value={example.extracted}
                                    onChange={(e) => {
                                      const globalIndex = (datapoint.examples || []).indexOf(example);
                                      updateExample(globalIndex, 'extracted', e.target.value);
                                    }}
                                    className="mt-2"
                                  />
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      
                      <Button
                        variant="outline"
                        onClick={() => addExample(activeExampleTab)}
                        className="w-full"
                      >
                        <Plus className="h-4 w-4 mr-2" />
                        Add {activeExampleTab} Example
                      </Button>
                    </div>
                    </TabsContent>
                  </Tabs>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <p>Enable few-shot prompting to add examples</p>
                  </div>
                )}
              </CardContent>
            </Card>

          {/* Checkpoint Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Checkpoint Configuration</CardTitle>
              <CardDescription>Save intermediate results during long extraction processes</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="output-directory">
                    Output Directory
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Info className="h-3 w-3 inline ml-1" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Directory where results and checkpoint will be saved</p>
                      </TooltipContent>
                    </Tooltip>
                  </Label>
                  <Input
                    id="output-directory"
                    type="text"
                    placeholder="./output"
                    value={outputDirectory}
                    onChange={(e) => setOutputDirectory(e.target.value)}
                    disabled={isExtracting}
                    className="mt-2"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Both final results and checkpoint file will be saved in this directory
                  </p>
                </div>
                
                <Separator />
                
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label htmlFor="enable-checkpoints">Enable Checkpoints</Label>
                    <p className="text-sm text-muted-foreground">Save intermediate results during processing</p>
                  </div>
                  <Switch
                    id="enable-checkpoints"
                    checked={enableCheckpoints}
                    onCheckedChange={setEnableCheckpoints}
                    disabled={isExtracting}
                  />
                </div>
                
                {enableCheckpoints && (
                  <div>
                    <Label htmlFor="save-frequency">
                      Save Checkpoint Every
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Info className="h-3 w-3 inline ml-1" />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Results will be saved after processing this many rows</p>
                        </TooltipContent>
                      </Tooltip>
                    </Label>
                    <div className="flex items-center gap-2 mt-2">
                      <Input
                        id="save-frequency"
                        type="number"
                        min="1"
                        max="1000"
                        value={saveFrequency}
                        onChange={(e) => {
                          const value = e.target.value;
                          if (value === '') {
                            setSaveFrequency(0); // Allow empty field temporarily
                          } else {
                            const num = parseInt(value);
                            if (!isNaN(num) && num >= 1) {
                              setSaveFrequency(num);
                            }
                          }
                        }}
                        onBlur={(e) => {
                          // On blur, if empty or 0, set to 1
                          if (!e.target.value || parseInt(e.target.value) < 1) {
                            setSaveFrequency(1);
                          }
                        }}
                        className="w-24"
                        disabled={isExtracting}
                      />
                      <span className="text-sm text-muted-foreground">rows</span>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Execution & Results */}
          <Card>
            <CardHeader>
              <CardTitle>Execution & Results</CardTitle>
              <CardDescription>Run the extraction process and download results</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">

                {!isExtracting ? (
                  <Button
                    className="w-full"
                    size="lg"
                    onClick={startExtraction}
                    disabled={
                      !uploadedFile || 
                      !textColumn || 
                      !datapoint.name || 
                      !datapoint.instruction || 
                      !llmModel
                    }
                  >
                    <Play className="h-5 w-5 mr-2" />
                    Start Extraction
                  </Button>
                ) : (
                  <Button
                    className="w-full"
                    size="lg"
                    onClick={stopExtraction}
                    variant="destructive"
                  >
                    <StopCircle className="h-5 w-5 mr-2" />
                    Stop Extraction
                  </Button>
                )}

                {/* Progress */}
                {extractionProgress && (
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">
                        {extractionProgress.message || 'Processing...'}
                      </span>
                      <span className="font-medium">
                        {extractionProgress.percentage.toFixed(1)}%
                      </span>
                    </div>
                    <Progress value={extractionProgress.percentage} className="[&>*]:bg-green-500" />
                    <p className="text-xs text-gray-500 text-center">
                      Row {extractionProgress.current_row} of {extractionProgress.total_rows}
                    </p>
                  </div>
                )}

                {/* Results */}
                {extractionResults && (
                  <div className="space-y-4">
                    <Alert>
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription>
                        Extraction completed successfully!
                      </AlertDescription>
                    </Alert>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-sm text-gray-600">Rows Processed</p>
                        <p className="text-2xl font-semibold">{extractionResults.rows_processed}</p>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-sm text-gray-600">Processing Time</p>
                        <p className="text-2xl font-semibold">
                          {extractionResults.processing_time 
                            ? (() => {
                                const seconds = extractionResults.processing_time;
                                if (seconds < 60) {
                                  return `${seconds.toFixed(1)}s`;
                                } else if (seconds < 3600) {
                                  const minutes = Math.floor(seconds / 60);
                                  const remainingSeconds = seconds % 60;
                                  return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
                                } else {
                                  const hours = Math.floor(seconds / 3600);
                                  const minutes = Math.floor((seconds % 3600) / 60);
                                  return `${hours}h ${minutes}m`;
                                }
                              })()
                            : 'N/A'}
                        </p>
                      </div>
                    </div>

                    {extractionResults.metrics && (
                      <div className="bg-blue-50 p-4 rounded-lg">
                        <h4 className="font-medium mb-2">Extraction Metrics</h4>
                        <div className="space-y-1 text-sm">
                          {Object.entries(extractionResults.metrics).map(([key, metrics]: [string, any]) => (
                            <div key={key} className="flex justify-between">
                              <span className="text-gray-600">Accuracy</span>
                              <span className="font-medium">{(metrics.accuracy * 100).toFixed(1)}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        className="flex-1"
                        onClick={() => downloadResults('csv')}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download CSV
                      </Button>
                      <Button
                        variant="outline"
                        className="flex-1"
                        onClick={() => downloadResults('excel')}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download Excel
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </main>
      </div>
    </TooltipProvider>
  );
}