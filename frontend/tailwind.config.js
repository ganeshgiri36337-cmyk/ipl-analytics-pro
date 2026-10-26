/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b1020",
        panel: "#121a2b",
        accent: "#9b8afb",
      },
    },
  },
  plugins: [],
};
