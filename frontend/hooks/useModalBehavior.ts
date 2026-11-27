import { useEffect, useRef, type RefObject } from 'react';

/**
 * Closes a modal on Escape, moves focus into it on open and returns focus to the
 * previously focused element on close. The Escape listener is removed on close and unmount.
 * The latest `onClose` is read through a ref, so an inline callback does not re-run the
 * effect (which would move focus again on every parent render).
 */
export function useModalBehavior(
  isOpen: boolean,
  onClose: () => void,
  containerRef: RefObject<HTMLElement | null>,
): void {
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!isOpen) {
      return undefined;
    }
    const opener = document.activeElement as HTMLElement | null;
    containerRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.key === 'Escape') {
        onCloseRef.current();
      }
    };
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      opener?.focus?.();
    };
  }, [isOpen, containerRef]);
}
