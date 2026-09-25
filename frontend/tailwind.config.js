/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Geist', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'IBM Plex Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        // Base surfaces (Premium Dark Theme)
        background: '#0A0C0F',
        surface: '#111418',
        surfaceHighlight: '#171B21',
        surfaceElevated: '#1D232B',
        border: 'rgba(255,255,255,0.08)',

        // Brand
        primary: {
          DEFAULT: '#18D6C1', // teal/mint
          hover: '#14B8A6',
          dim: 'rgba(24,214,193,0.12)',
        },
        accent: {
          DEFAULT: '#0EA5E9', // cyan
          hover: '#0284C7',
          dim: 'rgba(14,165,233,0.12)',
        },

        // Semantic
        success: {
          DEFAULT: '#10b981', // emerald
          dim: 'rgba(16,185,129,0.12)',
        },
        warning: {
          DEFAULT: '#f59e0b', // amber
          dim: 'rgba(245,158,11,0.12)',
        },
        danger: {
          DEFAULT: '#ef4444', // red
          dim: 'rgba(239,68,68,0.12)',
        },
        info: {
          DEFAULT: '#3b82f6', // blue
          dim: 'rgba(59,130,246,0.12)',
        },

        // Risk levels
        risk: {
          low: '#10b981',
          medium: '#f59e0b',
          high: '#f97316',
          critical: '#ef4444',
        },

        // Text
        text: {
          primary: '#f8fafc',
          secondary: '#cbd5e1',
          muted: '#8492a6',
          code: '#e2e8f0',
        },
      },

      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
      },

      boxShadow: {
        'glow-primary': '0 0 20px rgba(24,214,193,0.15)',
        'glow-danger': '0 0 20px rgba(239,68,68,0.15)',
        'glow-success': '0 0 20px rgba(16,185,129,0.15)',
        'card': '0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.4)',
        'modal': '0 25px 50px rgba(0,0,0,0.6)',
      },

      borderRadius: {
        'sm': '4px',
        DEFAULT: '6px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
        '2xl': '24px',
      },

      animation: {
        'fade-in': 'fadeIn 0.15s ease-out',
        'slide-up': 'slideUp 0.2s ease-out',
        'slide-down': 'slideDown 0.15s ease-out',
        'scale-in': 'scaleIn 0.15s ease-out',
        'pulse-slow': 'pulse 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 1.8s infinite',
        'spin-slow': 'spin 3s linear infinite',
      },

      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.97)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [],
};
