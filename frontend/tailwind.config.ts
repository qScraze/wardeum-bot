import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        bg: '#0A0A0A',
        surface: '#1C1C1E',
        surface2: '#2C2C2E',
        surface3: '#3A3A3C',
        border: 'rgba(255,255,255,0.08)',
        muted: 'rgba(255,255,255,0.45)',
        dim: 'rgba(255,255,255,0.25)',
      },
      borderRadius: {
        card: '16px',
        pill: '50px',
      },
      screens: {
        xs: '360px',
      },
    },
  },
  plugins: [],
} satisfies Config
