'use client';
import Link from 'next/link';
import BaseButton from '@/components/shared/BaseButton';
import { useRegisterForm, type RegisterField } from '@/hooks/useRegisterForm';

interface FieldConfig {
  id: RegisterField;
  label: string;
  type?: 'email' | 'password';
}

const FIELDS: FieldConfig[] = [
  { id: 'name', label: 'Name' },
  { id: 'username', label: 'Username' },
  { id: 'email', label: 'Email', type: 'email' },
  { id: 'password', label: 'Password', type: 'password' },
];

const inputClass = 'w-full rounded-lg border border-line bg-surface px-3 py-2 text-ink';

export default function RegisterPage() {
  const { values, errors, submitting, handleChange, handleSubmit } = useRegisterForm();

  return (
    <main className="mx-auto w-full max-w-md px-4 py-10">
      <h1 className="mb-6 text-2xl font-semibold text-ink">Create your account</h1>
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
        {FIELDS.map(({ id, label, type }) => (
          <div key={id}>
            <label htmlFor={id} className="mb-1 block text-sm text-ink">
              {label}
            </label>
            <input
              id={id}
              name={id}
              type={type}
              className={inputClass}
              value={values[id]}
              onChange={handleChange}
            />
            {errors[id] && (
              <p role="alert" className="mt-1 text-sm text-danger">
                {errors[id]}
              </p>
            )}
          </div>
        ))}
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
