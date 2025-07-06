"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { 
  X, Play, Square, Download, Trash2, RefreshCw, 
  FileText, Clock, CheckCircle, XCircle, Activity,
  BarChart3, Settings, AlertCircle 
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { jobsAPI, type Job } from "@/lib/api";
import { getStatusColor, formatDuration, formatBytes } from "@/lib/utils";

interface JobDetailsDialogProps {
  job: Job;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onJobUpdated: () => void;
}

export function JobDetailsDialog({ job, open, onOpenChange, onJobUpdated }: JobDetailsDialogProps) {
  const [activeTab, setActiveTab] = useState("overview");
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Fetch detailed job info
  const { data: jobDetails, refetch: refetchDetails } = useQuery({
    queryKey: ['job', job.job_id],
    queryFn: () => jobsAPI.get(job.job_id),
    enabled: open,
    refetchInterval: job.status === 'running' || job.status === 'processing' ? 2000 : false,
  });

  // Fetch results if completed
  const { data: results } = useQuery({
    queryKey: ['job-results', job.job_id],
    queryFn: () => jobsAPI.getResults(job.job_id),
    enabled: open && job.status === 'completed',
  });

  const currentJob = jobDetails || job;

  const handleStart = async () => {
    setActionLoading("start");
    try {
      await jobsAPI.start(currentJob.job_id);
      onJobUpdated();
      refetchDetails();
    } catch (error) {
      console.error('Error starting job:', error);
      alert('Error starting job');
    } finally {
      setActionLoading(null);
    }
  };

  const handleStop = async () => {
    setActionLoading("stop");
    try {
      await jobsAPI.stop(currentJob.job_id);
      onJobUpdated();
      refetchDetails();
    } catch (error) {
      console.error('Error stopping job:', error);
      alert('Error stopping job');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this job? This action cannot be undone.")) {
      return;
    }
    
    setActionLoading("delete");
    try {
      await jobsAPI.delete(currentJob.job_id);
      onJobUpdated();
      onOpenChange(false);
    } catch (error) {
      console.error('Error deleting job:', error);
      alert('Error deleting job');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDownload = async (format: 'csv' | 'excel') => {
    setActionLoading(`download-${format}`);
    try {
      const blob = await jobsAPI.downloadResults(currentJob.job_id, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${currentJob.name}_results.${format === 'excel' ? 'xlsx' : 'csv'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading results:', error);
      alert('Error downloading results');
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'running':
      case 'processing':
        return <Activity className="h-5 w-5 text-blue-600 animate-spin" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'created':
      case 'pending':
        return <Clock className="h-5 w-5 text-gray-600" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-600" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-3">
            {getStatusIcon(currentJob.status)}
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{currentJob.name}</h2>
              <p className="text-sm text-gray-500">Job ID: {currentJob.job_id}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => refetchDetails()}
              disabled={actionLoading === "refresh"}
            >
              <RefreshCw className={`h-4 w-4 ${actionLoading === "refresh" ? "animate-spin" : ""}`} />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Action Bar */}
        <div className="flex items-center justify-between p-6 bg-gray-50 border-b">
          <div className="flex items-center space-x-3">
            <Badge variant={
              currentJob.status === 'completed' ? 'success' :
              currentJob.status === 'running' || currentJob.status === 'processing' ? 'info' :
              currentJob.status === 'failed' ? 'destructive' : 'secondary'
            }>
              {currentJob.status}
            </Badge>
            {currentJob.progress_percentage > 0 && (
              <div className="flex items-center space-x-2">
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${currentJob.progress_percentage}%` }}
                  />
                </div>
                <span className="text-sm font-medium">{currentJob.progress_percentage}%</span>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            {currentJob.status === 'created' || currentJob.status === 'data_uploaded' ? (
              <Button 
                onClick={handleStart}
                disabled={actionLoading === "start"}
                className="medical-gradient"
              >
                <Play className="h-4 w-4 mr-2" />
                {actionLoading === "start" ? "Starting..." : "Start Job"}
              </Button>
            ) : currentJob.status === 'running' || currentJob.status === 'processing' ? (
              <Button 
                onClick={handleStop}
                disabled={actionLoading === "stop"}
                variant="outline"
              >
                <Square className="h-4 w-4 mr-2" />
                {actionLoading === "stop" ? "Stopping..." : "Stop Job"}
              </Button>
            ) : null}
            
            {currentJob.status === 'completed' && (
              <div className="flex items-center space-x-2">
                <Button 
                  onClick={() => handleDownload('csv')}
                  disabled={actionLoading?.startsWith('download')}
                  variant="outline"
                >
                  <Download className="h-4 w-4 mr-2" />
                  CSV
                </Button>
                <Button 
                  onClick={() => handleDownload('excel')}
                  disabled={actionLoading?.startsWith('download')}
                  variant="outline"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Excel
                </Button>
              </div>
            )}
            
            <Button 
              onClick={handleDelete}
              disabled={actionLoading === "delete" || currentJob.status === 'running'}
              variant="destructive"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              {actionLoading === "delete" ? "Deleting..." : "Delete"}
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <nav className="flex space-x-8 px-6">
            {[
              { id: "overview", label: "Overview", icon: FileText },
              { id: "progress", label: "Progress", icon: BarChart3 },
              { id: "config", label: "Configuration", icon: Settings },
              ...(currentJob.status === 'completed' ? [{ id: "results", label: "Results", icon: CheckCircle }] : [])
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-4 w-4 mr-2" />
                {label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium">Processing Status</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-gray-900">
                      {currentJob.processed_rows}/{currentJob.total_rows}
                    </div>
                    <p className="text-xs text-gray-500">rows processed</p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-green-600">
                      {currentJob.processed_rows > 0 ? 
                        Math.round((currentJob.successful_rows / currentJob.processed_rows) * 100) : 0}%
                    </div>
                    <p className="text-xs text-gray-500">
                      {currentJob.successful_rows} successful, {currentJob.failed_rows} failed
                    </p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium">Runtime</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-gray-900">
                      {currentJob.started_at ? formatDuration(
                        ((currentJob.completed_at ? new Date(currentJob.completed_at) : new Date()).getTime() - 
                         new Date(currentJob.started_at).getTime()) / 1000
                      ) : "Not started"}
                    </div>
                    <p className="text-xs text-gray-500">total runtime</p>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Job Timeline</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">Created</span>
                      <span className="text-gray-500">{formatTimestamp(currentJob.created_at)}</span>
                    </div>
                    {currentJob.started_at && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">Started</span>
                        <span className="text-gray-500">{formatTimestamp(currentJob.started_at)}</span>
                      </div>
                    )}
                    {currentJob.completed_at && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">Completed</span>
                        <span className="text-gray-500">{formatTimestamp(currentJob.completed_at)}</span>
                      </div>
                    )}
                    {currentJob.error_message && (
                      <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                        <p className="text-sm text-red-700 font-medium">Error:</p>
                        <p className="text-sm text-red-600">{currentJob.error_message}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Progress Tab */}
          {activeTab === "progress" && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Processing Progress</CardTitle>
                  <CardDescription>
                    Step {currentJob.current_step} of {currentJob.total_steps}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div 
                        className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                        style={{ width: `${currentJob.progress_percentage}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>0%</span>
                      <span className="font-medium">{currentJob.progress_percentage}%</span>
                      <span>100%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {currentJob.processing_stats && (
                <Card>
                  <CardHeader>
                    <CardTitle>Processing Statistics</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      {Object.entries(currentJob.processing_stats).map(([key, value]) => (
                        <div key={key} className="text-center">
                          <div className="text-lg font-semibold text-gray-900">
                            {typeof value === 'number' ? value : String(value)}
                          </div>
                          <div className="text-gray-500">
                            {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* Configuration Tab */}
          {activeTab === "config" && currentJob.config_snapshot && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Data Configuration</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Text Column:</span> {currentJob.config_snapshot.text_column}
                    </div>
                    {currentJob.config_snapshot.ground_truth_column && (
                      <div>
                        <span className="font-medium">Ground Truth:</span> {currentJob.config_snapshot.ground_truth_column}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Datapoints</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {currentJob.config_snapshot.datapoint_configs.map((dp: any, index: number) => (
                      <div key={index} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium">{dp.name}</h4>
                          <div className="flex space-x-2">
                            <Badge variant="outline">{dp.extraction_strategy}</Badge>
                            {dp.use_rag && <Badge variant="info">RAG</Badge>}
                          </div>
                        </div>
                        <p className="text-sm text-gray-600">{dp.prompt}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {currentJob.config_snapshot.llm_config && (
                <Card>
                  <CardHeader>
                    <CardTitle>LLM Configuration</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                      {Object.entries(currentJob.config_snapshot.llm_config).map(([key, value]) => (
                        <div key={key}>
                          <span className="font-medium">
                            {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                          </span>{' '}
                          {String(value)}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* Results Tab */}
          {activeTab === "results" && results && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Extraction Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {results.summary?.total_rows || 0}
                      </div>
                      <div className="text-sm text-gray-500">Total Rows</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {results.summary?.datapoints_extracted || 0}
                      </div>
                      <div className="text-sm text-gray-500">Datapoints Extracted</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {results.summary?.processing_time_seconds ? 
                          formatDuration(results.summary.processing_time_seconds) : "N/A"}
                      </div>
                      <div className="text-sm text-gray-500">Processing Time</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {results.evaluation && Object.keys(results.evaluation.datapoint_metrics || {}).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Evaluation Results</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {Object.entries(results.evaluation.datapoint_metrics).map(([dpName, metrics]: [string, any]) => (
                        <div key={dpName} className="border rounded-lg p-4">
                          <h4 className="font-medium mb-3">{dpName}</h4>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            {metrics.accuracy && Object.entries(metrics.accuracy).map(([metric, value]: [string, any]) => (
                              <div key={metric} className="text-center">
                                <div className="text-lg font-semibold">
                                  {typeof value === 'number' ? 
                                    (metric.includes('percentage') || metric.includes('accuracy') || metric.includes('precision') || metric.includes('recall') || metric.includes('f1') ? 
                                      `${(value * 100).toFixed(1)}%` : value.toFixed(3)) : 
                                    String(value)}
                                </div>
                                <div className="text-gray-500 capitalize">
                                  {metric.replace(/_/g, ' ')}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}