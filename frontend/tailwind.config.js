/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        agri: {
          bg: '#F4F7F4',        // Clean off-white natural background
          card: '#FFFFFF',      // Card surface
          cardSoft: '#F9FBF8',  // Soft warm card background
          border: '#D8E2D8',    // Soft sage border
          deep: '#1B5E20',      // Deep rice-green
          leaf: '#2E7D32',      // Vibrant leaf green
          sage: '#81C784',      // Soft sage green
          sageLight: '#E8F5E9', // Light sage background tint
          sageBorder: '#C8E6C9',// Sage border highlight
          earth: '#5D4037',     // Warm earth brown
          earthLight: '#D7CCC8',// Soft earth tint
          amber: '#E65100',     // Warm orange target accent
          sky: '#0288D1',       // Light sky blue
          skyLight: '#E1F5FE',  // Soft sky tint
          textDark: '#1C281D',  // Deep organic dark text
          textMuted: '#4A5D4C', // Muted sage text
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
