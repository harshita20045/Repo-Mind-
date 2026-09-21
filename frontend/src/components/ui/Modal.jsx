import React, { useEffect, useRef } from 'react';

export default function Modal({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  size = 'md',
  className = '',
}) {
  const overlayRef = useRef(null);
  const firstFocusRef = useRef(null);

  // Trap focus inside modal
  useEffect(() => {
    if (!isOpen) return;
    const previousFocus = document.activeElement;
    setTimeout(() => firstFocusRef.current?.focus(), 50);

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'Tab') {
        const modal = overlayRef.current?.querySelector('[data-modal-content]');
        if (!modal) return;
        const focusableEls = modal.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const first = focusableEls[0];
        const last = focusableEls[focusableEls.length - 1];
        if (e.shiftKey ? document.activeElement === first : document.activeElement === last) {
          e.preventDefault();
          (e.shiftKey ? last : first)?.focus();
        }
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
      previousFocus?.focus();
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizes = {
    sm:  'max-w-sm',
    md:  'max-w-md',
    lg:  'max-w-lg',
    xl:  'max-w-xl',
    '2xl': 'max-w-2xl',
  };

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        data-modal-content
        className={`relative w-full ${sizes[size] || sizes.md} bg-surface border border-white/10 rounded-2xl shadow-modal animate-scale-in ${className}`}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-white/[0.07]">
          <div>
            <h2
              id="modal-title"
              className="text-lg font-semibold text-text-primary"
              ref={firstFocusRef}
              tabIndex={-1}
            >
              {title}
            </h2>
            {subtitle && (
              <p className="text-sm text-text-muted mt-1">{subtitle}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="ml-4 p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-white/5 transition-colors flex-shrink-0"
            aria-label="Close modal"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  );
}
