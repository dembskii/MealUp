'use client';

import { AuthProvider } from './AuthContext';

export function AuthProviderWrapper({ children }) {
  return <AuthProvider>{children}</AuthProvider>;
}
