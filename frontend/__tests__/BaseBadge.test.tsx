import { render, screen } from '@testing-library/react';
import BaseBadge, { type BadgeColor } from '@/components/shared/BaseBadge';

const expected: Record<BadgeColor, string[]> = {
  gray: ['bg-surface-muted', 'text-ink-muted'],
  blue: ['bg-info-soft', 'text-ink'],
  green: ['bg-success-soft', 'text-ink'],
  yellow: ['bg-warning-soft', 'text-ink'],
  red: ['bg-danger-soft', 'text-ink'],
};

describe('BaseBadge', () => {
  it.each(Object.keys(expected) as BadgeColor[])('renders the %s color', (color) => {
    render(<BaseBadge color={color}>Label</BaseBadge>);
    expect(screen.getByText('Label')).toHaveClass(...expected[color]);
  });

  it('defaults to gray', () => {
    render(<BaseBadge>Default</BaseBadge>);
    expect(screen.getByText('Default')).toHaveClass('bg-surface-muted');
  });
});
