import type { ReactNode } from 'react';

export type BadgeColor = 'gray' | 'green' | 'yellow' | 'red' | 'blue';

const colorClasses: Record<BadgeColor, string> = {
  gray: 'bg-surface-muted text-ink-muted',
  blue: 'bg-info-soft text-ink',
  green: 'bg-success-soft text-ink',
  yellow: 'bg-warning-soft text-ink',
  red: 'bg-danger-soft text-ink',
};

/** Renders a short status label in one of five colors. */
interface BaseBadgeProps {
  color?: BadgeColor;
  children: ReactNode;
}

function BaseBadge({ color = 'gray', children }: BaseBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colorClasses[color]}`}
    >
      {children}
    </span>
  );
}

export default BaseBadge;
