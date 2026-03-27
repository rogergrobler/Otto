import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0a0a",
        accent: "#3b82f6",
        rag: {
          optimal: "#22c55e",
          normal: "#6b7280",
          borderline: "#f59e0b",
          high: "#ef4444",
          low: "#ef4444",
          insufficient: "#374151",
        },
      },
    },
  },
  plugins: [],
};

export default config;
