import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Manrope", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        card: "0 10px 24px rgba(15, 23, 42, 0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
