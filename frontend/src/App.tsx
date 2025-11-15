import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Dashboard } from './pages/Dashboard';
import { Login } from './pages/Login';
import { apiService } from './services/api';
import './App.css';

const AppContent: React.FC = () => {
  const { authenticated, loading, logout, token, keycloak } = useAuth();

  useEffect(() => {
    if (token) {
      apiService.setAuthToken(token);
    } else {
      apiService.removeAuthToken();
    }
  }, [token]);

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <Router>
      {authenticated && (
        <header className="app-header">
          <div className="container">
            <div className="header-content">
              <h1>NER Analysis</h1>
              <div className="user-info">
                <span>👤 {keycloak?.tokenParsed?.preferred_username}</span>
                <button onClick={logout} className="btn-small">
                  Logout
                </button>
              </div>
            </div>
          </div>
        </header>
      )}

      <Routes>
        <Route
          path="/"
          element={authenticated ? <Dashboard /> : <Navigate to="/login" />}
        />
        <Route
          path="/login"
          element={!authenticated ? <Login /> : <Navigate to="/" />}
        />
      </Routes>
    </Router>
  );
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
