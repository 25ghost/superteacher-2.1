/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Cormorant Garamond", "Georgia", "serif"],
        body: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        script: ["Caveat", "Segoe Print", "cursive"],
      },
      boxShadow: {
        paper: "0 24px 80px rgba(20, 10, 4, 0.45), inset 0 0 38px rgba(88, 45, 14, 0.18)",
        seal: "0 10px 22px rgba(64, 8, 5, 0.4), inset 0 2px 7px rgba(255,255,255,.23)",
      },
      colors: {
        ink: "#2e241d",
        umber: "#6b3e22",
        paper: "#e7d4ab",
        moss: "#405946",
        tealink: "#315963",
        wax: "#7f1516",
      },
    },
  },
  plugins: [],
};
