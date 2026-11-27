'use client';
import { useState, type ChangeEvent, type FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import BaseButton from '@/components/shared/BaseButton';
import { useAuth } from '@/context/AuthContext';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { apiClient } from '@/lib/apiClient';
import { ApiError } from '@/lib/errors';
import type { LoginResult } from '@/types/api';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface FieldErrors {
  email?: string;
  password?: string;
}

const inputClass = 'w-full rounded-lg border border-line bg-surface px-3 py-2 text-ink';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const { handleError } = useErrorHandler();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleEmailChange = (e: ChangeEvent<HTMLInputElement>): void => setEmail(e.target.value);
  const handlePasswordChange = (e: ChangeEvent<HTMLInputElement>): void =>
    setPassword(e.target.value);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setFormError(null);
    const found: FieldErrors = {};
    if (!EMAIL_PATTERN.test(email)) found.email = 'Enter a valid email';
    if (password.length === 0) found.password = 'Password is required';
    setErrors(found);
    if (Object.keys(found).length > 0) return;
    setSubmitting(true);
    try {
      const result = await apiClient.post<LoginResult>('/api/auth/login', { email, password });
      login(result.access_token, result.user);
      router.push('/');
    } catch (err) {
      if (err instanceof ApiError && err.statusCode === 401) {
        setFormError(err.message);
      } else {
        handleError(err, { isLoginRequest: true });
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="mx-auto w-full max-w-md px-4 py-10">
      <h1 className="mb-6 text-2xl font-semibold text-ink">Log in</h1>
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
        {formError && (
          <p role="alert" className="text-sm text-danger">
            {formError}
          </p>
        )}
        <div>
          <label htmlFor="email" className="mb-1 block text-sm text-ink">
            Email
          </label>
          <input
            id="email"
            type="email"
            className={inputClass}
            value={email}
            onChange={handleEmailChange}
          />
          {errors.email && (
            <p role="alert" className="mt-1 text-sm text-danger">
              {errors.email}
            </p>
          )}
        </div>
        <div>
          <label htmlFor="password" className="mb-1 block text-sm text-ink">
            Password
          </label>
          <input
            id="password"
            type="password"
            className={inputClass}
            value={password}
            onChange={handlePasswordChange}
          />
          {errors.password && (
            <p role="alert" className="mt-1 text-sm text-danger">
              {errors.password}
            </p>
          )}
        </div>
        <BaseButton type="submit" variant="primary" disabled={submitting}>
          Log in
        </BaseButton>
      </form>
      <p className="mt-4 text-sm text-ink-muted">
        No account yet?{' '}
        <Link href="/register" className="text-primary underline">
          Register
        </Link>
      </p>
    </main>
  );
}
