import React from 'react';

const BASE = 'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60 focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:opacity-50 disabled:cursor-not-allowed select-none';

const SIZE = {
  xs: 'px-2.5 py-1 text-xs rounded-md',
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-2.5 text-base',
};

const VARIANT = {
  primary:   'bg-primary hover:bg-primary-hover text-white shadow-sm shadow-primary/20 border border-primary/30',
  secondary: 'bg-surfaceHighlight hover:bg-surfaceElevated text-text-primary border border-white/10',
  ghost:     'bg-transparent hover:bg-white/5 text-text-secondary hover:text-text-primary border border-transparent hover:border-white/10',
  danger:    'bg-danger/10 hover:bg-danger/20 text-danger border border-danger/25',
  'danger-solid': 'bg-danger hover:bg-danger/90 text-white border border-white/10 shadow-sm shadow-danger/20',
  success:   'bg-success/10 hover:bg-success/20 text-success border border-success/25',
  'success-solid': 'bg-success hover:bg-success/90 text-white border border-white/10 shadow-sm shadow-success/20',
  outline:   'bg-transparent hover:bg-white/5 text-text-primary border border-white/15 hover:border-white/25',
  accent:    'bg-accent/10 hover:bg-accent/20 text-accent border border-accent/25',
};

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  leftIcon = null,
  rightIcon = null,
  className = '',
  ...props
}) {
  return (
    <button
      className={`${BASE} ${SIZE[size] || SIZE.md} ${VARIANT[variant] || VARIANT.primary} ${className}`}
      disabled={disabled || loading}
      aria-busy={loading}
      {...props}
    >
      {loading ? (
        <svg
          className="w-4 h-4 animate-spin flex-shrink-0"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
      ) : leftIcon ? (
        <span className="flex-shrink-0 w-4 h-4" aria-hidden="true">{leftIcon}</span>
      ) : null}
      {children}
      {!loading && rightIcon && (
        <span className="flex-shrink-0 w-4 h-4" aria-hidden="true">{rightIcon}</span>
      )}
    </button>
  );
}

// Icon-only button
export function IconButton({
  children,
  variant = 'ghost',
  size = 'md',
  label,
  className = '',
  ...props
}) {
  const sizes = { sm: 'p-1.5', md: 'p-2', lg: 'p-2.5' };
  return (
    <button
      className={`${BASE} rounded-lg ${sizes[size] || sizes.md} ${VARIANT[variant] || VARIANT.ghost} ${className}`}
      aria-label={label}
      {...props}
    >
      {children}
    </button>
  );
}
