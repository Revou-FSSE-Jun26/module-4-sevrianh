import React from 'react';
import { render, screen } from '@testing-library/react';
import KanbanBoard from '@/components/board/KanbanBoard';
import type { BoardDetail } from '@/types/api';

jest.mock('next/navigation', () => ({ useRouter: () => ({ refresh: jest.fn() }) }));
jest.mock('@/context/AuthContext', () => ({ useAuth: () => ({ token: 'tok' }) }));
jest.mock('@/hooks/useErrorHandler', () => ({ useErrorHandler: () => ({ handleError: jest.fn() }) }));
jest.mock('@/lib/apiClient', () => ({ apiClient: { patch: jest.fn(), post: jest.fn(), delete: jest.fn() } }));

const board: BoardDetail = {
  id: 'b1',
  name: 'Test Board',
  team_id: 't1',
  created_at: '2024-01-01',
  columns: [
    { id: 'c1', name: 'Todo', order: 1, is_done: false, cards: [] },
    { id: 'c2', name: 'Done', order: 2, is_done: true, cards: [] },
  ],
};

describe('KanbanBoard', () => {
  it('renders columns in order', () => {
    render(<KanbanBoard initialBoard={board} isReadOnly={false} isAdmin={true} members={[]} />);
    const headings = screen.getAllByRole('heading', { level: 3 });
    expect(headings[0]).toHaveTextContent('Todo');
    expect(headings[1]).toHaveTextContent('Done');
  });

  it('shows Add Column button for admin', () => {
    render(<KanbanBoard initialBoard={board} isReadOnly={false} isAdmin={true} members={[]} />);
    expect(screen.getByRole('button', { name: /add column/i })).toBeInTheDocument();
  });

  it('hides Add Column button when readOnly', () => {
    render(<KanbanBoard initialBoard={board} isReadOnly={true} isAdmin={false} members={[]} />);
    expect(screen.queryByRole('button', { name: /add column/i })).not.toBeInTheDocument();
  });

  it('shows no draggable handles in readOnly mode', () => {
    render(<KanbanBoard initialBoard={board} isReadOnly={true} isAdmin={false} members={[]} />);
    const draggable = document.querySelector('[draggable="true"]');
    expect(draggable).not.toBeInTheDocument();
  });
});
