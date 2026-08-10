/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0a0908",
          900: "#100f0d",
          850: "#161412",
          800: "#1c1a17",
          700: "#282521",
          600: "#39352f",
          500: "#4d473f",
        },
        paper: {
          100: "#f6f2e9",
          200: "#ece5d4",
          300: "#d8cfba",
          400: "#a89e8b",
          500: "#7c7367",
        },
        ember: {
          300: "#f6bd8a",
          400: "#f0a463",
          500: "#e2884a",
          600: "#c06b36",
          700: "#96522a",
        },
        sage: {
          300: "#b7d4c4",
          400: "#8fbfa8",
          500: "#68a488",
          600: "#4f8269",
        },
        rust: {
          400: "#e2897a",
          500: "#cc6a58",
          600: "#a84f40",
        },
      },
      fontFamily: {
        display: ["'Fraunces'", "ui-serif", "Georgia", "serif"],
        sans: ["'Inter'", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 0 0 rgba(246,242,233,0.04) inset, 0 20px 40px -24px rgba(0,0,0,0.6)",
        lift: "0 12px 32px -12px rgba(0,0,0,0.55)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: 0, transform: "translateY(6px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
        blink: {
          "0%, 100%": { opacity: 1 },
          "50%": { opacity: 0.15 },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.35s cubic-bezier(0.16,1,0.3,1) both",
        blink: "blink 1s step-start infinite",
        shimmer: "shimmer 2.2s linear infinite",
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
