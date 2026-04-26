/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#050713",
        panel: "#0a1020",
        panelSoft: "#0e1830",
        line: "#263b72",
        cyanLine: "#2f7ce8",
        neon: "#ff4fcf",
        neonSoft: "#ff86dd",
        text: "#eaf1ff",
        muted: "#91a7d0"
      },
      boxShadow: {
        neon: "0 0 26px rgba(255, 79, 207, 0.18)",
        panel: "0 18px 60px rgba(0, 0, 0, 0.35)"
      }
    }
  },
  plugins: []
};
