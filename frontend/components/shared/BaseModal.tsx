'use client';

import { useId, useRef, type ReactNode } from 'react';
import BaseButton from '@/components/shared/BaseButton';
import { useModalBehavior } from '@/hooks/useModalBehavior';

/** Renders a dialog overlay with a title, a close button and its content. */
interface BaseModalProps {
  isOpen: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}

function BaseModal({ isOpen, title, onClose, children }: BaseModalProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const titleId = useId();
  useModalBehavior(isOpen, onClose, containerRef);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/50 p-4">
      <div
        ref={containerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className="max-h-full w-full max-w-lg overflow-y-auto rounded-lg bg-surface p-4 text-ink shadow-lg focus-visible:outline-none md:p-6"
      >
        <div className="mb-4 flex items-center justify-between gap-2">
          <h2 id={titleId} className="text-lg font-semibold">
            {title}
          </h2>
          <BaseButton variant="secondary" aria-label="Close" onClick={onClose}>
            ×
          </BaseButton>
        </div>
        {children}
      </div>
    </div>
  );
}

export default BaseModal;
