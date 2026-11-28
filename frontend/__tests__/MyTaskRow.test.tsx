import React from 'react';
import { render, screen } from '@testing-library/react';
import MyTaskRow from '@/components/card/MyTaskRow';
import type { CardListItem } from '@/types/api';

const task: CardListItem = {
  id: 'card1',
  title: 'Write unit tests',
  order: 1,
  column_id: 'c1',
  column_name: 'In Review',
  board_id: 'b1',
  board_name: 'Sprint 1',
  assignee_id: 'u1',
  assignee: { id: 'u1', name: 'Alice', username: 'alice' },
};

describe('MyTaskRow', () => {
  it('renders card title', () => {
    render(<ul><MyTaskRow card={task} /></ul>);
    expect(screen.getByText('Write unit tests')).toBeInTheDocument();
  });

  it('renders board name', () => {
    render(<ul><MyTaskRow card={task} /></ul>);
    expect(screen.getByText('Sprint 1')).toBeInTheDocument();
  });

  it('renders column name as badge', () => {
    render(<ul><MyTaskRow card={task} /></ul>);
    expect(screen.getByText('In Review')).toBeInTheDocument();
  });

  it('renders link to board with card query param', () => {
    render(<ul><MyTaskRow card={task} /></ul>);
    const link = screen.getByRole('link', { name: /view/i });
    expect(link).toHaveAttribute('href', '/boards/b1?card=card1');
  });
});
