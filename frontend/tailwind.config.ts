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
    },
  },
} satisfies Config

