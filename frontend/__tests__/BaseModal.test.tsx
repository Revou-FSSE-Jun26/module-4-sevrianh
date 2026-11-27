import { useState } from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import BaseModal from '@/components/shared/BaseModal';

function Harness() {
  const [isOpen, setIsOpen] = useState(false);
  const handleOpen = (): void => setIsOpen(true);
  const handleClose = (): void => setIsOpen(false);
  return (
    <>
      <button onClick={handleOpen}>Open</button>
      <BaseModal isOpen={isOpen} title="Edit card" onClose={handleClose}>
        <input aria-label="Title" />
      </BaseModal>
    </>
  );
}

describe('BaseModal', () => {
  it('renders nothing when closed', () => {
    render(
      <BaseModal isOpen={false} title="Hidden" onClose={jest.fn()}>
        content
      </BaseModal>,
    );
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('renders an aria-modal dialog labelled by its title and moves focus into it', () => {
    render(
      <BaseModal isOpen title="Edit card" onClose={jest.fn()}>
        content
      </BaseModal>,
    );
    const dialog = screen.getByRole('dialog', { name: 'Edit card' });
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveFocus();
  });

  it('closes on Escape and returns focus to the opener', () => {
    render(<Harness />);
    const opener = screen.getByRole('button', { name: 'Open' });
    opener.focus();
    fireEvent.click(opener);
    expect(screen.getByRole('dialog')).toHaveFocus();

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(opener).toHaveFocus();
  });

  it('closes through the labelled close button', () => {
    const handleClose = jest.fn();
    render(
      <BaseModal isOpen title="Edit card" onClose={handleClose}>
        content
      </BaseModal>,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
