'use client';
import { useState, type ChangeEvent, type FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import BaseButton from '@/components/shared/BaseButton';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { apiClient } from '@/lib/apiClient';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const USERNAME_PATTERN = /^[A-Za-z0-9_]{3,30}$/;

interface FieldErrors {
  name?: string;
  username?: string;
  email?: string;
  password?: string;
}

function validate(name: string, username: string, email: string, password: string): FieldErrors {
  const errors: FieldErrors = {};
  if (name.trim().length < 1 || name.length > 100)
    errors.name = 'Name is required (1-100 characters)';
  if (!USERNAME_PATTERN.test(username)) {
    errors.username = 'Username must be 3-30 letters, digits or underscores';
  }
  if (!EMAIL_PATTERN.test(email) || email.length > 254) errors.email = 'Enter a valid email';
  if (password.length < 8 || password.length > 128) {
    errors.password = 'Password must be 8-128 characters';
  }
  return errors;
}

const inputClass = 'w-full rounded-lg border border-line bg-surface px-3 py-2 text-ink';

export default function RegisterPage() {
  const router = useRouter();
  const { handleError } = useErrorHandler();
  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitting, setSubmitting] = useState(false);

  const handleNameChange = (e: ChangeEvent<HTMLInputElement>): void => setName(e.target.value);
  const handleUsernameChange = (e: ChangeEvent<HTMLInputElement>): void =>
    setUsername(e.target.value);
  const handleEmailChange = (e: ChangeEvent<HTMLInputElement>): void => setEmail(e.target.value);
  const handlePasswordChange = (e: ChangeEvent<HTMLInputElement>): void =>
    setPassword(e.target.value);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    const found = validate(name, username, email, password);
    setErrors(found);
    if (Object.keys(found).length > 0) return;
    setSubmitting(true);
    try {
      await apiClient.post('/api/auth/register', { name: name.trim(), username, email, password });
      router.push('/login');
    } catch (err) {
      handleError(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="mx-auto w-full max-w-md px-4 py-10">
      <h1 className="mb-6 text-2xl font-semibold text-ink">Create your account</h1>
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
        <div>
          <label htmlFor="name" className="mb-1 block text-sm text-ink">
            Name
          </label>
          <input id="name" className={inputClass} value={name} onChange={handleNameChange} />
          {errors.name && (
            <p role="alert" className="mt-1 text-sm text-danger">
              {errors.name}
            </p>
          )}
        </div>
        <div>
          <label htmlFor="username" className="mb-1 block text-sm text-ink">
            Username
          </label>
          <input
            id="username"
            className={inputClass}
            value={username}
            onChange={handleUsernameChange}
          />
          {errors.username && (
            <p role="alert" className="mt-1 text-sm text-danger">
              {errors.username}
            </p>
          )}
        </div>
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
          Register
        </BaseButton>
      </form>
      <p className="mt-4 text-sm text-ink-muted">
        Already have an account?{' '}
        <Link href="/login" className="text-primary underline">
          Log in
        </Link>
      </p>
    </main>
  );
}
