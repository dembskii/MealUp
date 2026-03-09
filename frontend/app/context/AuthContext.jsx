'use client';

import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/auth/me', {
        credentials: 'include',
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      } else {
        setUser(null);
        document.cookie = 'session_id=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const handleLogin = () => {
    window.location.href = 'http://localhost:8000/api/v1/auth/login';
  };

  const handleSignUp = (role = 'user') => {
    window.location.href = `http://localhost:8000/api/v1/auth/login?prompt=signup&role=${role}`;
  };

  const handleLogout = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/auth/logout', {
        method: 'GET',
        credentials: 'include',
      });
      if (res.ok) {
        const data = await res.json();
        setUser(null);
        if (data.logout_url) {
          window.location.href = data.logout_url;
        } else {
          window.location.reload();
        }
      } else {
        setUser(null);
        window.location.reload();
      }
    } catch {
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        handleLogin,
        handleSignUp,
        handleLogout,
        refreshAuth: checkAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
