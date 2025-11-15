export interface DocumentMetadata {
  document_id: string;
  filename: string;
  document_type: 'pdf' | 'image' | 'text';
  size_bytes: number;
  uploaded_at: string;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  minio_path: string;
  user_id: string;
  processed_at?: string;
  error_message?: string;
}

export interface EntityGroup {
  tag: string;
  human_readable_tag: string;
  entities: string[];
  count: number;
}

export interface SentenceAnalysis {
  sentence_index: number;
  text: string;
  tokens: string[];
  predictions: Array<[string, string]>;
  tag_counts: { [key: string]: number };
  entities: EntityGroup[];
}

export interface AnalysisResult {
  analysis_id: string;
  document_id: string;
  user_id: string;
  created_at: string;
  processing_time_seconds: number;
  llm_extracted_text?: string;
  llm_processing_time?: number;
  total_sentences: number;
  total_tokens: number;
  sentence_analyses: SentenceAnalysis[];
  overall_tag_counts: { [key: string]: number };
  all_entities: EntityGroup[];
}

export interface AnalysisStatus {
  analysis_id: string;
  document_id: string;
  status: string;
  created_at: string;
  completed_at?: string;
  error_message?: string;
}
