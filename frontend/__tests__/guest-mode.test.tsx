import React from 'react';
import { render, screen } from '@testing-library/react';
import KanbanBoard from '@/components/board/KanbanBoard';
import type { BoardDetail } from '@/types/api';

jest.mock('next/navigation', () => ({ useRouter: () => ({ refresh: jest.fn() }) }));
jest.mock('@/context/AuthContext', () => ({ useAuth: () => ({ token: null }) }));
jest.mock('@/hooks/useErrorHandler', () => ({ useErrorHandler: () => ({ handleError: jest.fn() }) }));
jest.mock('@/lib/apiClient', () => ({ apiClient: { patch: jest.fn(), post: jest.fn(), delete: jest.fn() } }));

const board: BoardDetail = {
  id: 'b1',
  name: 'Guest Board',
  team_id: 't1',
  created_at: '2024-01-01',
  columns: [
    {
      id: 'c1',
      name: 'Backlog',
      order: 1,
      is_done: false,
      cards: [
        {
          id: 'card1',
          title: 'Sample Card',
          description: '',
          order: 1,
          column_id: 'c1',
          assignee_id: null,
          assignee: null,
          created_by_id: 'u1',
          completed_at: null,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
      ],
    },
  ],
};

describe('Guest Mode (read-only KanbanBoard)', () => {
  it('renders columns and cards without draggable handles', () => {
    render(<KanbanBoard initialBoard={board} isReadOnly={true} isAdmin={false} members={[]} />);
    expect(screen.getByText('Sample Card')).toBeInTheDocument();
    const draggable = document.querySelector('[draggable="true"]');
    expect(draggable).not.toBeInTheDocument();
  });

  it('shows no "Add Card" buttons in read-only mode', () => {
    render(<KanbanBoard initialBoard={board} isReadOnly={true} isAdmin={false} members={[]} />);
    expect(screen.queryByRole('button', { name: /add card/i })).not.toBeInTheDocument();
  });

  it('shows no "Add Column" button in read-only mode', () => {
    render(<KanbanBoard initialBoard={board} isReadOnly={true} isAdmin={false} members={[]} />);
    expect(screen.queryByRole('button', { name: /add column/i })).not.toBeInTheDocument();
  });

  it('shows no edit buttons on column headers in read-only mode', () => {
    render(<KanbanBoard initialBoard={board} isReadOnly={true} isAdmin={false} members={[]} />);
    expect(screen.queryByLabelText(/rename column/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/delete column/i)).not.toBeInTheDocument();
  });
});
