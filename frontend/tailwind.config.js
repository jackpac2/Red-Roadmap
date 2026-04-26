/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#07100b",
        panel: "#111a12",
        panelSoft: "#1a2418",
        line: "#3a422f",
        cyanLine: "#786f42",
        neon: "#b7a85b",
        neonSoft: "#eadfb7",
        text: "#f3ead7",
        muted: "#b7aa8a",
        forest: "#0d160f",
        gold: "#c69a49",
        moss: "#6f7a37"
      },
      boxShadow: {
        neon: "0 0 26px rgba(198, 154, 73, 0.16)",
        panel: "0 18px 60px rgba(0, 0, 0, 0.38)"
      }
    }
  },
  plugins: []
};
