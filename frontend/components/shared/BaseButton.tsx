import type { ButtonHTMLAttributes, ReactNode } from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'destructive';

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'bg-primary text-white hover:bg-primary-hover',
  secondary: 'bg-secondary text-ink hover:bg-secondary-hover',
  destructive: 'bg-danger text-white hover:opacity-90',
};

type NativeButtonProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'>;

/** Renders the one button element of the application in a fixed variant. */
type BaseButtonProps = NativeButtonProps & {
  variant?: ButtonVariant;
} & (
    { children: ReactNode; 'aria-label'?: string } | { children?: undefined; 'aria-label': string }
  );

function BaseButton({
  variant = 'primary',
  type = 'button',
  className = '',
  children,
  ...rest
}: BaseButtonProps) {
  const classes = `inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50 ${variantClasses[variant]} ${className}`;
  return (
    <button type={type} className={classes.trim()} {...rest}>
      {children}
    </button>
  );
}

export default BaseButton;
