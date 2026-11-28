import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import CommentList from '@/components/comments/CommentList';
import { apiClient } from '@/lib/apiClient';
import type { Comment } from '@/types/api';

jest.mock('@/context/AuthContext', () => ({
  useAuth: () => ({ token: 'tok', user: { id: 'user1' } }),
}));
jest.mock('@/hooks/useErrorHandler', () => ({ useErrorHandler: () => ({ handleError: jest.fn() }) }));
jest.mock('@/lib/apiClient', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  },
}));

const baseComment: Comment = {
  id: 'cm1',
  card_id: 'card1',
  parent_id: null,
  author_id: 'user1',
  content: 'Hello world',
  is_deleted: false,
  created_at: '2024-01-01T10:00:00Z',
  updated_at: '2024-01-01T10:00:00Z',
};

const editedComment: Comment = {
  ...baseComment,
  id: 'cm2',
  content: 'Edited content',
  updated_at: '2024-01-02T10:00:00Z',
};

const deletedWithReply: Comment = {
  ...baseComment,
  id: 'cm3',
  content: 'Was here',
  is_deleted: true,
};

const reply: Comment = {
  ...baseComment,
  id: 'cm4',
  parent_id: 'cm3',
  content: 'Still here reply',
};

describe('CommentList', () => {
  beforeEach(() => {
    jest.mocked(apiClient.post).mockResolvedValue({ ...baseComment, id: 'cmnew', content: 'New comment' });
  });

  it('renders comments loaded from API', async () => {
    jest.mocked(apiClient.get).mockResolvedValue([baseComment]);
    render(<CommentList cardId="card1" isReadOnly={false} />);
    await waitFor(() => expect(screen.getByText('Hello world')).toBeInTheDocument());
  });

  it('shows "edited" label for updated comments', async () => {
    jest.mocked(apiClient.get).mockResolvedValue([editedComment]);
    render(<CommentList cardId="card1" isReadOnly={false} />);
    await waitFor(() => expect(screen.getByText('edited')).toBeInTheDocument());
  });

  it('shows tombstone for deleted comment with active reply', async () => {
    jest.mocked(apiClient.get).mockResolvedValue([deletedWithReply, reply]);
    render(<CommentList cardId="card1" isReadOnly={false} />);
    await waitFor(() => expect(screen.getByText(/this comment was deleted/i)).toBeInTheDocument());
    expect(screen.getByText('Still here reply')).toBeInTheDocument();
  });

  it('omits deleted comment with no replies', async () => {
    const deleted: Comment = { ...baseComment, id: 'cm5', is_deleted: true };
    jest.mocked(apiClient.get).mockResolvedValue([deleted]);
    render(<CommentList cardId="card1" isReadOnly={false} />);
    await waitFor(() => expect(screen.queryByText(/this comment was deleted/i)).not.toBeInTheDocument());
  });

  it('hides comment form in readOnly mode', async () => {
    jest.mocked(apiClient.get).mockResolvedValue([]);
    render(<CommentList cardId="card1" isReadOnly={true} />);
    await waitFor(() => expect(screen.queryByPlaceholderText(/add a comment/i)).not.toBeInTheDocument());
  });
});
