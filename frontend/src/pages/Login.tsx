import React from 'react';
import { useAuth } from '../contexts/AuthContext';

export const Login: React.FC = () => {
  const { login } = useAuth();

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-card">
          <h1>NER Document Analysis</h1>
          <p className="subtitle">Named Entity Recognition with LLM preprocessing</p>

          <div className="features">
            <div className="feature">
              <span className="icon">📄</span>
              <span>Upload PDF, Images, or Text</span>
            </div>
            <div className="feature">
              <span className="icon">🤖</span>
              <span>AI-powered text extraction</span>
            </div>
            <div className="feature">
              <span className="icon">🏷️</span>
              <span>Named Entity Recognition</span>
            </div>
          </div>

          <button onClick={login} className="btn-login">
            Sign In with Keycloak
          </button>

          <p className="help-text">
            Secure authentication powered by Keycloak
          </p>
        </div>
      </div>
    </div>
  );
};
