import React, { useState, useEffect } from 'react';
import { DocumentUpload } from '../components/DocumentUpload';
import { DocumentList } from '../components/DocumentList';
import { AnalysisResults } from '../components/AnalysisResults';
import { apiService } from '../services/api';
import { DocumentMetadata, AnalysisResult, AnalysisStatus } from '../types';

export const Dashboard: React.FC = () => {
  const [refreshDocuments, setRefreshDocuments] = useState(false);
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResult | null>(null);
  const [analyzingDocId, setAnalyzingDocId] = useState<string | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUploadSuccess = (document: DocumentMetadata) => {
    console.log('Document uploaded:', document);
    setRefreshDocuments(!refreshDocuments);
  };

  const handleAnalyze = async (documentId: string) => {
    setError(null);
    setCurrentAnalysis(null);
    setAnalyzingDocId(documentId);

    try {
      const status = await apiService.createAnalysis(documentId, true);
      setAnalysisStatus(status);
      pollAnalysisStatus(status.analysis_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create analysis');
      setAnalyzingDocId(null);
    }
  };

  const pollAnalysisStatus = async (analysisId: string) => {
    const maxAttempts = 60; // 2 minutes max
    let attempts = 0;

    const interval = setInterval(async () => {
      attempts++;

      try {
        const status = await apiService.getAnalysisStatus(analysisId);
        setAnalysisStatus(status);

        if (status.status === 'completed') {
          clearInterval(interval);
          const result = await apiService.getAnalysisResult(analysisId);
          setCurrentAnalysis(result);
          setAnalyzingDocId(null);
          setRefreshDocuments(!refreshDocuments);
        } else if (status.status === 'failed') {
          clearInterval(interval);
          setError(status.error_message || 'Analysis failed');
          setAnalyzingDocId(null);
        } else if (attempts >= maxAttempts) {
          clearInterval(interval);
          setError('Analysis timeout - taking too long');
          setAnalyzingDocId(null);
        }
      } catch (err: any) {
        console.error('Error polling status:', err);
        if (attempts >= 3) {
          clearInterval(interval);
          setError('Failed to check analysis status');
          setAnalyzingDocId(null);
        }
      }
    }, 2000); // Poll every 2 seconds
  };

  return (
    <div className="dashboard">
      <div className="container">
        <h1>NER Document Analysis</h1>

        <div className="grid-2col">
          <div className="card">
            <DocumentUpload onUploadSuccess={handleUploadSuccess} />
          </div>

          {analyzingDocId && (
            <div className="card">
              <div className="analysis-progress">
                <h3>⏳ Analyzing Document...</h3>
                {analysisStatus && (
                  <div>
                    <p>Status: <strong>{analysisStatus.status}</strong></p>
                    <p className="help-text">
                      {analysisStatus.status === 'queued' && 'Waiting in queue...'}
                      {analysisStatus.status === 'processing' && 'Processing with LLM and NER...'}
                    </p>
                  </div>
                )}
                <div className="spinner"></div>
              </div>
            </div>
          )}
        </div>

        {error && (
          <div className="card error-card">
            <strong>Error:</strong> {error}
          </div>
        )}

        <div className="card">
          <DocumentList refresh={refreshDocuments} onAnalyze={handleAnalyze} />
        </div>

        {currentAnalysis && (
          <div className="card">
            <AnalysisResults result={currentAnalysis} />
          </div>
        )}
      </div>
    </div>
  );
};
