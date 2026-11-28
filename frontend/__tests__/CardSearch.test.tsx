import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import CardSearch from '@/components/card/CardSearch';
import { useCardSearch } from '@/hooks/useCardSearch';

jest.mock('@/context/AuthContext', () => ({ useAuth: () => ({ token: 'tok' }) }));
jest.mock('@/hooks/useErrorHandler', () => ({ useErrorHandler: () => ({ handleError: jest.fn() }) }));

const mockResults = [
  { id: 'card1', title: 'Fix login bug', order: 1, column_id: 'c1', column_name: 'In Progress', board_id: 'b1', board_name: 'Sprint 1', assignee_id: null, assignee: null },
];

jest.mock('@/hooks/useCardSearch', () => ({
  useCardSearch: jest.fn(),
  SEARCH_DEBOUNCE_MS: 300,
}));

describe('CardSearch', () => {
  beforeEach(() => {
    jest.mocked(useCardSearch).mockReturnValue({ results: [], isLoading: false });
  });

  it('renders search input', () => {
    render(<CardSearch boardId="b1" />);
    expect(screen.getByRole('searchbox')).toBeInTheDocument();
  });

  it('shows empty state when term has no results', () => {
    jest.mocked(useCardSearch).mockReturnValue({ results: [], isLoading: false });
    render(<CardSearch boardId="b1" />);
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'missing' } });
    expect(screen.getByText('No cards found.')).toBeInTheDocument();
  });

  it('shows results list when search returns items', async () => {
    jest.mocked(useCardSearch).mockReturnValue({ results: mockResults, isLoading: false });
    render(<CardSearch boardId="b1" />);
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'login' } });
    await waitFor(() => expect(screen.getByText('Fix login bug')).toBeInTheDocument());
    expect(screen.getByText('In Progress')).toBeInTheDocument();
  });

  it('shows loading indicator when isLoading is true', () => {
    jest.mocked(useCardSearch).mockReturnValue({ results: [], isLoading: true });
    render(<CardSearch boardId="b1" />);
    expect(screen.getByText('Searching…')).toBeInTheDocument();
  });

  it('result links point to board with card query', async () => {
    jest.mocked(useCardSearch).mockReturnValue({ results: mockResults, isLoading: false });
    render(<CardSearch boardId="b1" />);
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'login' } });
    await waitFor(() => {
      const link = screen.getByRole('link', { name: /fix login bug/i });
      expect(link).toHaveAttribute('href', '/boards/b1?card=card1');
    });
  });
});
