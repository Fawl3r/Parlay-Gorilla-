import type { Config } from 'tailwindcss'

export default {
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Logo green palette - matching newlogo.png
        'logo-green': {
          DEFAULT: '#00FF5E', // Primary logo green
          '50': '#E6FFF2',
          '100': '#CCFFE5',
          '200': '#99FFCB',
          '300': '#66FFB1',
          '400': '#33FF97',
          '500': '#00FF5E', // Logo green
          '600': '#00CC4B', // Logo fill
          '700': '#009938',
          '800': '#006625',
          '900': '#003312',
        },
        // Override emerald to match logo green
        'emerald': {
          '50': '#E6FFF2',
          '100': '#CCFFE5',
          '200': '#99FFCB',
          '300': '#66FFB1',
          '400': '#33FF97',
          '500': '#00FF5E', // Logo green (was emerald-500)
          '600': '#00CC4B', // Logo fill (was emerald-600)
          '700': '#009938',
          '800': '#006625',
          '900': '#003312',
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      transitionDuration: {
        'fast': '150ms',
        'normal': '200ms',
        'slow': '300ms',
        'slower': '400ms',
        'slowest': '600ms',
      },
      transitionTimingFunction: {
        'spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
} satisfies Config

