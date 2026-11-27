import { useRef } from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { useModalBehavior } from '@/hooks/useModalBehavior';

interface HarnessProps {
  isOpen: boolean;
  onClose: () => void;
}

function Harness({ isOpen, onClose }: HarnessProps) {
  const ref = useRef<HTMLDivElement>(null);
  useModalBehavior(isOpen, onClose, ref);
  return (
    <>
      <button>Opener</button>
      <div ref={ref} tabIndex={-1} data-testid="box" />
    </>
  );
}

describe('useModalBehavior', () => {
  it('moves focus into the container when opened', () => {
    render(<Harness isOpen onClose={jest.fn()} />);
    expect(screen.getByTestId('box')).toHaveFocus();
  });

  it('calls onClose on Escape and ignores other keys', () => {
    const onClose = jest.fn();
    render(<Harness isOpen onClose={onClose} />);
    fireEvent.keyDown(document, { key: 'Enter' });
    expect(onClose).not.toHaveBeenCalled();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('returns focus to the opener when closed', () => {
    const { rerender } = render(<Harness isOpen={false} onClose={jest.fn()} />);
    const opener = screen.getByRole('button', { name: 'Opener' });
    opener.focus();
    rerender(<Harness isOpen onClose={jest.fn()} />);
    expect(screen.getByTestId('box')).toHaveFocus();
    rerender(<Harness isOpen={false} onClose={jest.fn()} />);
    expect(opener).toHaveFocus();
  });

  it('does not steal focus again when only onClose changes', () => {
    const { rerender } = render(<Harness isOpen onClose={jest.fn()} />);
    const box = screen.getByTestId('box');
    screen.getByRole('button', { name: 'Opener' }).focus();
    rerender(<Harness isOpen onClose={jest.fn()} />);
    expect(box).not.toHaveFocus();
  });

  it('uses the latest onClose and removes the listener when closed or unmounted', () => {
    const first = jest.fn();
    const second = jest.fn();
    const { rerender, unmount } = render(<Harness isOpen onClose={first} />);
    rerender(<Harness isOpen onClose={second} />);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(first).not.toHaveBeenCalled();
    expect(second).toHaveBeenCalledTimes(1);

    rerender(<Harness isOpen={false} onClose={second} />);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(second).toHaveBeenCalledTimes(1);

    rerender(<Harness isOpen onClose={second} />);
    unmount();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(second).toHaveBeenCalledTimes(1);
  });
});
