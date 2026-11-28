'use client';

import type { DragEvent } from 'react';

interface Props {
  cardId: string;
  onDragStart: (e: DragEvent, cardId: string) => void;
  onDragEnd: () => void;
}

/** The only component that sets the `draggable` attribute (FE-28). */
export default function CardDragHandle({ cardId, onDragStart, onDragEnd }: Props) {
  return (
    <span
      draggable
      onDragStart={(e) => onDragStart(e, cardId)}
      onDragEnd={onDragEnd}
      className="cursor-grab px-1 text-gray-400 hover:text-gray-600 active:cursor-grabbing"
      aria-label="Drag to reorder"
      role="button"
      tabIndex={0}
    >
      ⠿
    </span>
  );
}
