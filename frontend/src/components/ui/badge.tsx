import * as React from 'react';
import { cn } from '@/lib/utils';

const Badge = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { variant?: 'default' | 'secondary' | 'destructive' | 'outline' }
>(({ className, variant = 'default', ...props }, ref) => {
  const variantClasses = {
    default: 'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]',
    secondary: 'bg-[hsl(var(--secondary))] text-[hsl(var(--secondary-foreground))]',
    destructive: 'bg-[hsl(var(--destructive))] text-[hsl(var(--destructive-foreground))]',
    outline: 'border border-[hsl(var(--border))] text-[hsl(var(--foreground))]',
  };
  return (
    <div
      ref={ref}
      className={cn(
        'inline-flex items-center rounded-md px-2.5 py-0.5 text-xs font-semibold transition-colors',
        variantClasses[variant],
        className
      )}
      {...props}
    />
  );
});
Badge.displayName = 'Badge';

export { Badge };
