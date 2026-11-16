/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#716FA6",
          "primary-dark": "#58568c",
          secondary: "#BBC8F2",
          "secondary-light": "#e8edfd",
          warning: "#F2EFC4",
          "warning-dark": "#a19934",
          dark: "#2c2c34",
          charcoal: "#595959",
          silver: "#BFBFBF",
          canvas: "#F6F7FB",
          surface: "#FFFFFF",
          surfaceAlt: "#F1F3F9",
        },
      },
      fontFamily: {
        sans: ["'Plus Jakarta Sans'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
        tech: ["'Space Mono'", "monospace"],
      },
    },
  },
  plugins: [],
}

