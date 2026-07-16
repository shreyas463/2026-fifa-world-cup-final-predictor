/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        pitch: {
          50: "#eefdf3",
          100: "#d6f9e2",
          400: "#28c76f",
          500: "#12a150",
          600: "#0c7d3d",
          900: "#05371c",
        },
        night: {
          800: "#111827",
          850: "#0d1424",
          900: "#0a0f1c",
          950: "#060a14",
        },
        gold: "#f4c542",
      },
      fontFamily: {
        display: ["Poppins", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
