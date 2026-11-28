import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import ProfilePage from '@/app/profile/page';
import { apiClient } from '@/lib/apiClient';

const mockUpdateUser = jest.fn();
const mockUser = { id: 'u1', name: 'Alice', username: 'alice', email: 'alice@example.com', created_at: '' };

jest.mock('@/context/AuthContext', () => ({
  useAuth: () => ({ token: 'tok', user: mockUser, updateUser: mockUpdateUser }),
}));
jest.mock('@/hooks/useErrorHandler', () => ({ useErrorHandler: () => ({ handleError: jest.fn() }) }));
jest.mock('@/lib/apiClient', () => ({
  apiClient: {
    patch: jest.fn(),
  },
}));

describe('ProfilePage', () => {
  beforeEach(() => {
    mockUpdateUser.mockClear();
    jest.mocked(apiClient.patch).mockResolvedValue({ ...mockUser, name: 'Alice Updated' });
  });

  it('pre-populates form with current user data', () => {
    render(<ProfilePage />);
    expect(screen.getByDisplayValue('Alice')).toBeInTheDocument();
    expect(screen.getByDisplayValue('alice@example.com')).toBeInTheDocument();
  });

  it('renders username as read-only', () => {
    render(<ProfilePage />);
    const usernameInput = screen.getByDisplayValue('alice');
    expect(usernameInput).toBeDisabled();
  });

  it('shows success message after save', async () => {
    render(<ProfilePage />);
    fireEvent.change(screen.getByLabelText(/^name$/i), { target: { value: 'Alice Updated' } });
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }));
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent(/updated successfully/i));
    expect(mockUpdateUser).toHaveBeenCalledWith(expect.objectContaining({ name: 'Alice Updated' }));
  });

  it('calls PATCH /api/users/me with updated data', async () => {
    render(<ProfilePage />);
    fireEvent.change(screen.getByLabelText(/^name$/i), { target: { value: 'Bob' } });
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }));
    await waitFor(() => expect(apiClient.patch).toHaveBeenCalledWith(
      '/api/users/me',
      { name: 'Bob', email: 'alice@example.com' },
      { token: 'tok' },
    ));
  });
});
