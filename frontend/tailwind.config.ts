import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"DM Mono"', 'monospace'],
      },
      colors: {
        bg: '#080c18',
        surface: '#0f1624',
        surface2: '#161f30',
        border: '#1a2840',
        border2: '#243452',
        accent: '#3b82f6',
        accent2: '#60a5fa',
        danger: '#ef4444',
        success: '#22c55e',
        warn: '#f59e0b',
        t1: '#f1f5f9',
        t2: '#94a3b8',
        t3: '#475569',
        chip: '#0f2444',
        chipTxt: '#93c5fd',
        chipBdr: '#1d4ed8',
      },
      boxShadow: {
        panel: '0 1px 1px rgba(0,0,0,0.18), 0 4px 12px rgba(0,0,0,0.28), 0 16px 40px rgba(0,0,0,0.22)',
        'panel-hover':
          '0 2px 2px rgba(0,0,0,0.22), 0 8px 24px rgba(0,0,0,0.38), 0 24px 56px rgba(0,0,0,0.28)',
        'accent-glow': '0 0 36px rgba(59,130,246,0.14)',
      },
      backdropBlur: {
        glass: '24px',
      },
      letterSpacing: {
        'tighter-xl': '-0.045em',
        'tighter-lg': '-0.03em',
      },
      animation: {
        'fade-up': 'fadeUp 0.3s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
        'pulse-dot': 'pulseDot 1.2s ease-in-out infinite',
        'bar-grow': 'barGrow 0.6s ease-out forwards',
        'slide-in': 'slideIn 0.25s ease-out',
      },
      keyframes: {
        fadeUp: {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'none' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        pulseDot: {
          '0%,80%,100%': { transform: 'scale(0.6)', opacity: '0.3' },
          '40%': { transform: 'scale(1)', opacity: '1' },
        },
        barGrow: {
          from: { width: '0%' },
          to: { width: 'var(--bar-width)' },
        },
        slideIn: {
          from: { opacity: '0', transform: 'translateX(-8px)' },
          to: { opacity: '1', transform: 'none' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
