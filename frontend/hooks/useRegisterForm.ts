'use client';
import { useState, type ChangeEvent, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { apiClient } from '@/lib/apiClient';

export type RegisterField = 'name' | 'username' | 'email' | 'password';
export type RegisterValues = Record<RegisterField, string>;
export type RegisterErrors = Partial<Record<RegisterField, string>>;

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const USERNAME_PATTERN = /^[A-Za-z0-9_]{3,30}$/;
const EMPTY_VALUES: RegisterValues = { name: '', username: '', email: '', password: '' };

/** Mirrors the server rules of backend.md BE-05 (RegisterSchema). */
export function validateRegister(values: RegisterValues): RegisterErrors {
  const errors: RegisterErrors = {};
  if (values.name.trim().length < 1 || values.name.length > 100) {
    errors.name = 'Name is required (1-100 characters)';
  }
  if (!USERNAME_PATTERN.test(values.username)) {
    errors.username = 'Username must be 3-30 letters, digits or underscores';
  }
  if (!EMAIL_PATTERN.test(values.email) || values.email.length > 254) {
    errors.email = 'Enter a valid email';
  }
  if (values.password.length < 8 || values.password.length > 128) {
    errors.password = 'Password must be 8-128 characters';
  }
  return errors;
}

interface UseRegisterForm {
  values: RegisterValues;
  errors: RegisterErrors;
  submitting: boolean;
  handleChange: (e: ChangeEvent<HTMLInputElement>) => void;
  handleSubmit: (e: FormEvent<HTMLFormElement>) => Promise<void>;
}

export function useRegisterForm(): UseRegisterForm {
  const router = useRouter();
  const { handleError } = useErrorHandler();
  const [values, setValues] = useState<RegisterValues>(EMPTY_VALUES);
  const [errors, setErrors] = useState<RegisterErrors>({});
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e: ChangeEvent<HTMLInputElement>): void => {
    const field = e.target.name as RegisterField;
    setValues((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    const found = validateRegister(values);
    setErrors(found);
    if (Object.keys(found).length > 0) return;
    setSubmitting(true);
    try {
      await apiClient.post('/api/auth/register', { ...values, name: values.name.trim() });
      router.push('/login');
    } catch (err) {
      handleError(err);
    } finally {
      setSubmitting(false);
    }
  };

  return { values, errors, submitting, handleChange, handleSubmit };
}
