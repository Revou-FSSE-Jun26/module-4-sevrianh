import './globals.css';
import type { Metadata } from 'next';
import { Suspense, type ReactNode } from 'react';
import Header from '@/components/layout/Header';
import { cookies } from 'next/headers';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from '@/context/AuthContext';
import { apiClient } from '@/lib/apiClient';
import type { User } from '@/types/api';

export const metadata: Metadata = {
  title: 'Sevy',
  description: 'Team task management boards',
};

async function loadInitialUser(token: string): Promise<User | null> {
  try {
    return await apiClient.get<User>('/api/users/me', { token });
  } catch {
    return null;
  }
}

export default async function RootLayout({ children }: { children: ReactNode }) {
  const token = (await cookies()).get('sevy_token')?.value ?? null;
  const initialUser = token ? await loadInitialUser(token) : null;
  const initialToken = initialUser ? token : null;

  return (
    <html lang="en">
      <body>
        <AuthProvider initialToken={initialToken} initialUser={initialUser}>
          <Suspense fallback={null}>
            <Header />
          </Suspense>
          {children}
        </AuthProvider>
        <Toaster />
      </body>
    </html>
  );
}
