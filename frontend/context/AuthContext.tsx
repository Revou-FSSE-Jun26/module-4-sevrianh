'use client';

import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import type { User } from '@/types/api';

export const TOKEN_COOKIE = 'sevy_token';
const TOKEN_MAX_AGE_SECONDS = 3600;

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  updateUser: (user: User) => void;
}

interface AuthProviderProps {
  children: ReactNode;
  initialToken?: string | null;
  initialUser?: User | null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function writeTokenCookie(token: string): void {
  document.cookie = `${TOKEN_COOKIE}=${encodeURIComponent(token)}; path=/; SameSite=Lax; max-age=${TOKEN_MAX_AGE_SECONDS}`;
}

function clearTokenCookie(): void {
  document.cookie = `${TOKEN_COOKIE}=; path=/; SameSite=Lax; max-age=0`;
}

export function AuthProvider({
  children,
  initialToken = null,
  initialUser = null,
}: AuthProviderProps) {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(initialToken);
  const [user, setUser] = useState<User | null>(initialUser);

  const login = useCallback((newToken: string, newUser: User): void => {
    setToken(newToken);
    setUser(newUser);
    writeTokenCookie(newToken);
  }, []);

  const logout = useCallback((): void => {
    setToken(null);
    setUser(null);
    clearTokenCookie();
    router.replace('/login');
  }, [router]);

  const updateUser = useCallback((newUser: User): void => {
    setUser(newUser);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, token, isAuthenticated: token !== null, login, logout, updateUser }),
    [user, token, login, logout, updateUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
