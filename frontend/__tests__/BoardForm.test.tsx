import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import BoardForm from '@/components/board/BoardForm';
import { apiClient } from '@/lib/apiClient';

jest.mock('next/navigation', () => ({ useRouter: () => ({ refresh: jest.fn() }) }));
jest.mock('@/context/AuthContext', () => ({ useAuth: () => ({ token: 'tok' }) }));
jest.mock('@/hooks/useErrorHandler', () => ({ useErrorHandler: () => ({ handleError: jest.fn() }) }));
jest.mock('@/lib/apiClient', () => ({
  apiClient: { post: jest.fn().mockResolvedValue({ id: '1', name: 'New', team_id: 't1', created_at: '' }) },
}));

describe('BoardForm', () => {
  it('shows validation error when name is empty', async () => {
    const onClose = jest.fn();
    render(<BoardForm onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: /create board/i }));
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Board name is required'));
    expect(onClose).not.toHaveBeenCalled();
  });

  it('shows validation error when name exceeds 100 chars', async () => {
    const onClose = jest.fn();
    render(<BoardForm onClose={onClose} />);
    fireEvent.change(screen.getByLabelText(/board name/i), { target: { value: 'x'.repeat(101) } });
    fireEvent.click(screen.getByRole('button', { name: /create board/i }));
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('100 characters'));
    expect(onClose).not.toHaveBeenCalled();
  });

  it('calls apiClient.post and closes on valid submission', async () => {
    const onClose = jest.fn();
    render(<BoardForm onClose={onClose} />);
    fireEvent.change(screen.getByLabelText(/board name/i), { target: { value: 'Sprint 1' } });
    fireEvent.click(screen.getByRole('button', { name: /create board/i }));
    await waitFor(() => expect(apiClient.post).toHaveBeenCalledWith(
      '/api/boards',
      { name: 'Sprint 1' },
      { token: 'tok' },
    ));
    await waitFor(() => expect(onClose).toHaveBeenCalled());
  });

  it('renders cancel button that closes without submitting', () => {
    const onClose = jest.fn();
    render(<BoardForm onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
    expect(onClose).toHaveBeenCalled();
  });
});
