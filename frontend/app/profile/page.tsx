'use client';

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { apiClient } from '@/lib/apiClient';
import BaseButton from '@/components/shared/BaseButton';
import type { User } from '@/types/api';

export default function ProfilePage() {
  const { user, token, updateUser } = useAuth();
  const { handleError } = useErrorHandler();
  const [name, setName] = useState(user?.name ?? '');
  const [email, setEmail] = useState(user?.email ?? '');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  if (!user) return <p className="p-8 text-gray-500">Loading…</p>;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSuccess(false);
    setSubmitting(true);
    try {
      const updated = await apiClient.patch<User>('/api/users/me', { name: name.trim(), email: email.trim() }, { token });
      updateUser(updated);
      setSuccess(true);
    } catch (err) {
      handleError(err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto max-w-md px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-800">Profile</h1>
      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        <div>
          <label htmlFor="profile-username" className="mb-1 block text-sm font-medium text-gray-700">
            Username <span className="text-gray-400">(read-only)</span>
          </label>
          <input
            id="profile-username"
            type="text"
            value={user.username}
            readOnly
            disabled
            className="min-h-11 w-full rounded border border-gray-200 bg-gray-100 px-3 py-2 text-sm text-gray-500"
          />
        </div>
        <div>
          <label htmlFor="profile-name" className="mb-1 block text-sm font-medium text-gray-700">Name</label>
          <input
            id="profile-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="min-h-11 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label htmlFor="profile-email" className="mb-1 block text-sm font-medium text-gray-700">Email</label>
          <input
            id="profile-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="min-h-11 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        {success && (
          <p role="status" className="text-sm text-green-600">Profile updated successfully!</p>
        )}
        <BaseButton type="submit" variant="primary" disabled={submitting} className="w-full">
          {submitting ? 'Saving…' : 'Save Changes'}
        </BaseButton>
      </form>
    </main>
  );
}
