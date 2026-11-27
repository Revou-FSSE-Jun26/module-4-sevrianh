import { fireEvent, render, screen } from '@testing-library/react';
import BaseButton from '@/components/shared/BaseButton';

describe('BaseButton', () => {
  it('renders the primary variant by default', () => {
    render(<BaseButton>Save</BaseButton>);
    const button = screen.getByRole('button', { name: 'Save' });
    expect(button).toHaveClass('bg-primary', 'text-white', 'hover:bg-primary-hover');
    expect(button).toHaveAttribute('type', 'button');
  });

  it('renders the secondary variant', () => {
    render(<BaseButton variant="secondary">Cancel</BaseButton>);
    expect(screen.getByRole('button', { name: 'Cancel' })).toHaveClass(
      'bg-secondary',
      'text-ink',
      'hover:bg-secondary-hover',
    );
  });

  it('renders the destructive variant', () => {
    render(<BaseButton variant="destructive">Delete</BaseButton>);
    expect(screen.getByRole('button', { name: 'Delete' })).toHaveClass('bg-danger', 'text-white');
  });

  it('defines focus-visible ring and disabled styles', () => {
    render(<BaseButton disabled>Save</BaseButton>);
    const button = screen.getByRole('button', { name: 'Save' });
    expect(button).toBeDisabled();
    expect(button).toHaveClass('focus-visible:ring-2', 'disabled:opacity-50');
  });

  it('calls onClick and exposes aria-label for an icon-only button', () => {
    const handleClick = jest.fn();
    render(<BaseButton aria-label="Close" onClick={handleClick} />);
    fireEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
