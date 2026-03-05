/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#4A6FA5',
          hover: '#3D5A8A',
          light: '#7BA3D1',
          lighter: '#DDEAF3',
          lightest: '#EBF4F9',
        },
        secondary: {
          DEFAULT: '#F2E8DF',
          hover: '#E8D9CA',
          border: '#DDCBB5',
        },
        heading: '#1C3B6B',
        text: {
          primary: '#2D3A52',
          secondary: '#5A6C7D',
          hint: '#A0B4C7',
          disabled: '#C5D0DC',
        },
        bg: {
          main: '#F4F7F9',
          card: '#FFFFFF',
          hover: '#F8FBFE',
        },
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"SF Pro Text"',
          '"SF Pro Display"',
          '"Helvetica Neue"',
          'sans-serif',
        ],
      },
      boxShadow: {
        'sm': '0 1px 3px rgba(28, 59, 107, 0.08)',
        'md': '0 2px 8px rgba(28, 59, 107, 0.08)',
        'lg': '0 4px 16px rgba(28, 59, 107, 0.12)',
        'xl': '0 8px 24px rgba(28, 59, 107, 0.15)',
      },
      borderRadius: {
        'sm': '8px',
        'md': '12px',
        'lg': '16px',
        'xl': '20px',
      },
    },
  },
  plugins: [],
}
