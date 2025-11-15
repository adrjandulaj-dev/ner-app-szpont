import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import { DocumentMetadata } from '../types';

interface DocumentListProps {
  refresh: boolean;
  onAnalyze: (documentId: string) => void;
}

export const DocumentList: React.FC<DocumentListProps> = ({ refresh, onAnalyze }) => {
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDocuments();
  }, [refresh]);

  const loadDocuments = async () => {
    setLoading(true);
    setError(null);

    try {
      const docs = await apiService.listDocuments(0, 50);
      setDocuments(docs);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (documentId: string) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      await apiService.deleteDocument(documentId);
      loadDocuments();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete document');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const getStatusBadge = (status: string) => {
    const colors: { [key: string]: string } = {
      uploaded: '#6c757d',
      processing: '#0d6efd',
      completed: '#198754',
      failed: '#dc3545',
    };

    return (
      <span
        style={{
          padding: '4px 8px',
          borderRadius: '4px',
          backgroundColor: colors[status] || '#6c757d',
          color: 'white',
          fontSize: '12px',
          fontWeight: 'bold',
        }}
      >
        {status.toUpperCase()}
      </span>
    );
  };

  if (loading) {
    return <div className="loading">Loading documents...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (documents.length === 0) {
    return <div className="empty-state">No documents uploaded yet</div>;
  }

  return (
    <div className="document-list">
      <h2>My Documents ({documents.length})</h2>
      <table>
        <thead>
          <tr>
            <th>Filename</th>
            <th>Type</th>
            <th>Size</th>
            <th>Status</th>
            <th>Uploaded</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr key={doc.document_id}>
              <td>{doc.filename}</td>
              <td>
                <span className="badge">{doc.document_type.toUpperCase()}</span>
              </td>
              <td>{formatFileSize(doc.size_bytes)}</td>
              <td>{getStatusBadge(doc.status)}</td>
              <td>{formatDate(doc.uploaded_at)}</td>
              <td>
                <button
                  onClick={() => onAnalyze(doc.document_id)}
                  className="btn-small btn-primary"
                  disabled={doc.status === 'processing'}
                >
                  Analyze
                </button>
                <button
                  onClick={() => handleDelete(doc.document_id)}
                  className="btn-small btn-danger"
                  style={{ marginLeft: '8px' }}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
