import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#111827',
        mist: '#f8fafc',
        line: '#dbe3ef',
        accent: '#0f766e',
      },
      boxShadow: {
        panel: '0 24px 60px -28px rgba(15, 23, 42, 0.3)',
      },
    },
  },
  plugins: [],
} satisfies Config
