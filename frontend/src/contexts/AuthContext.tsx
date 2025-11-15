import React, { createContext, useContext, useEffect, useState } from 'react';
import Keycloak from 'keycloak-js';

interface AuthContextType {
  keycloak: Keycloak | null;
  authenticated: boolean;
  loading: boolean;
  token: string | undefined;
  login: () => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  keycloak: null,
  authenticated: false,
  loading: true,
  token: undefined,
  login: () => {},
  logout: () => {},
});

export const useAuth = () => useContext(AuthContext);

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [keycloak, setKeycloak] = useState<Keycloak | null>(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const keycloakInstance = new Keycloak({
      url: process.env.REACT_APP_KEYCLOAK_URL || 'http://localhost:8080',
      realm: process.env.REACT_APP_KEYCLOAK_REALM || 'ner-app',
      clientId: process.env.REACT_APP_KEYCLOAK_CLIENT_ID || 'ner-frontend',
    });

    keycloakInstance
      .init({
        onLoad: 'check-sso',
        silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
        checkLoginIframe: false,
      })
      .then((authenticated) => {
        setKeycloak(keycloakInstance);
        setAuthenticated(authenticated);
        setLoading(false);

        // Refresh token periodically
        if (authenticated) {
          setInterval(() => {
            keycloakInstance.updateToken(70).catch(() => {
              console.error('Failed to refresh token');
            });
          }, 60000);
        }
      })
      .catch((error) => {
        console.error('Keycloak initialization failed:', error);
        setLoading(false);
      });
  }, []);

  const login = () => {
    keycloak?.login();
  };

  const logout = () => {
    keycloak?.logout();
  };

  return (
    <AuthContext.Provider
      value={{
        keycloak,
        authenticated,
        loading,
        token: keycloak?.token,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
