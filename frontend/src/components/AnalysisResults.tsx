import React from 'react';
import { AnalysisResult } from '../types';

interface AnalysisResultsProps {
  result: AnalysisResult;
}

export const AnalysisResults: React.FC<AnalysisResultsProps> = ({ result }) => {
  const formatDuration = (seconds: number) => {
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
    return `${seconds.toFixed(2)}s`;
  };

  const getTagColor = (tag: string): string => {
    const colors: { [key: string]: string } = {
      per: '#e74c3c',
      org: '#3498db',
      geo: '#2ecc71',
      gpe: '#f39c12',
      tim: '#9b59b6',
      art: '#1abc9c',
      nat: '#e67e22',
      eve: '#34495e',
    };
    return colors[tag] || '#95a5a6';
  };

  return (
    <div className="analysis-results">
      <div className="results-header">
        <h2>Analysis Results</h2>
        <div className="metadata">
          <span>⏱️ Processing time: {formatDuration(result.processing_time_seconds)}</span>
          {result.llm_processing_time && (
            <span>🤖 LLM extraction: {formatDuration(result.llm_processing_time)}</span>
          )}
          <span>📄 {result.total_sentences} sentences</span>
          <span>🔤 {result.total_tokens} tokens</span>
        </div>
      </div>

      {result.llm_extracted_text && (
        <div className="extracted-text">
          <h3>Extracted Text (LLM)</h3>
          <div className="text-box">
            {result.llm_extracted_text}
          </div>
        </div>
      )}

      <div className="entities-summary">
        <h3>Named Entities Found</h3>
        <div className="entity-groups">
          {result.all_entities.map((group, idx) => (
            <div
              key={idx}
              className="entity-group"
              style={{ borderLeft: `4px solid ${getTagColor(group.tag)}` }}
            >
              <div className="entity-header">
                <span className="entity-tag">{group.human_readable_tag}</span>
                <span className="entity-count">{group.count} found</span>
              </div>
              <div className="entity-items">
                {group.entities.map((entity, i) => (
                  <span
                    key={i}
                    className="entity-badge"
                    style={{ backgroundColor: getTagColor(group.tag) }}
                  >
                    {entity}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="sentence-analyses">
        <h3>Detailed Analysis by Sentence</h3>
        {result.sentence_analyses.map((sentence) => (
          <div key={sentence.sentence_index} className="sentence-card">
            <div className="sentence-header">
              <strong>Sentence {sentence.sentence_index + 1}</strong>
              <span className="token-count">{sentence.tokens.length} tokens</span>
            </div>
            <p className="sentence-text">{sentence.text}</p>

            {sentence.entities.length > 0 && (
              <div className="sentence-entities">
                <strong>Entities:</strong>
                {sentence.entities.map((group, idx) => (
                  <div key={idx} className="inline-entities">
                    <span className="inline-tag">{group.human_readable_tag}:</span>
                    {group.entities.map((entity, i) => (
                      <span
                        key={i}
                        className="entity-badge small"
                        style={{ backgroundColor: getTagColor(group.tag) }}
                      >
                        {entity}
                      </span>
                    ))}
                  </div>
                ))}
              </div>
            )}

            <details className="token-details">
              <summary>View tagged tokens</summary>
              <div className="tagged-tokens">
                {sentence.predictions.map(([word, tag], idx) => (
                  <span
                    key={idx}
                    className={`token ${tag !== 'O' ? 'tagged' : ''}`}
                    title={tag}
                  >
                    {word}
                    {tag !== 'O' && <sub>{tag}</sub>}
                  </span>
                ))}
              </div>
            </details>
          </div>
        ))}
      </div>
    </div>
  );
};
