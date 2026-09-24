/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        // Base surfaces
        background: '#0b0f1a',
        surface: '#111827',
        surfaceHighlight: '#1f2937',
        surfaceElevated: '#263347',
        border: 'rgba(255,255,255,0.08)',

        // Brand
        primary: {
          DEFAULT: '#14b8a6', // teal-500
          hover: '#0d9488',   // teal-600
          dim: 'rgba(20,184,166,0.12)',
        },
        accent: {
          DEFAULT: '#818cf8', // indigo-400
          hover: '#6366f1',   // indigo-500
          dim: 'rgba(129,140,248,0.12)',
        },

        // Semantic
        success: {
          DEFAULT: '#10b981', // emerald-500
          dim: 'rgba(16,185,129,0.12)',
        },
        warning: {
          DEFAULT: '#f59e0b', // amber-500
          dim: 'rgba(245,158,11,0.12)',
        },
        danger: {
          DEFAULT: '#f43f5e', // rose-500
          dim: 'rgba(244,63,94,0.12)',
        },
        info: {
          DEFAULT: '#38bdf8', // sky-400
          dim: 'rgba(56,189,248,0.12)',
        },

        // Risk levels
        risk: {
          low: '#10b981',
          medium: '#f59e0b',
          high: '#f97316',
          critical: '#f43f5e',
        },

        // Text
        text: {
          primary: '#f1f5f9',
          secondary: '#94a3b8',
          muted: '#64748b',
          code: '#e2e8f0',
        },
      },

      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
      },

      boxShadow: {
        'glow-primary': '0 0 20px rgba(20,184,166,0.15)',
        'glow-danger': '0 0 20px rgba(244,63,94,0.15)',
        'glow-success': '0 0 20px rgba(16,185,129,0.15)',
        'card': '0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.4)',
        'modal': '0 25px 50px rgba(0,0,0,0.6)',
      },

      borderRadius: {
        'xl': '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
      },

      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.2s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'pulse-slow': 'pulse 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 1.8s infinite',
        'spin-slow': 'spin 3s linear infinite',
        'bounce-subtle': 'bounceDots 1.4s infinite',
      },

      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.96)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        bounceDots: {
          '0%, 80%, 100%': { transform: 'scale(0.8)', opacity: '0.5' },
          '40%': { transform: 'scale(1)', opacity: '1' },
        },
      },

      backgroundImage: {
        'shimmer-gradient': 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.04) 50%, transparent 100%)',
      },
    },
  },
  plugins: [],
};
