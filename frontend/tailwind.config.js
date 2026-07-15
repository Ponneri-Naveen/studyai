/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f5f8ff',
          100: '#ebf1ff',
          200: '#d6e4ff',
          300: '#adc8ff',
          400: '#84a9ff',
          500: '#668eff',
          600: '#3b66f5',
          700: '#2b4ec7',
          800: '#1d3599',
          900: '#11206b',
          950: '#0a103d',
        },
        dark: {
          50: '#f6f6f9',
          100: '#ececf3',
          200: '#d5d6e3',
          300: '#b1b2cb',
          400: '#888aac',
          500: '#686a91',
          600: '#525477',
          700: '#434461',
          800: '#393a51',
          900: '#323244',
          950: '#181822',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
