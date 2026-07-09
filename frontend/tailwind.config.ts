import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        neutral: {
          50: "#f8faf9",
          100: "#eef2f1",
          200: "#d9e0de",
          300: "#b8c4c1",
          400: "#879693",
          500: "#5f6f6b",
          600: "#43524f",
          700: "#303d3a",
          800: "#1d2825",
          900: "#111816",
          950: "#090d0c"
        },
        accent: {
          50: "#effcf7",
          100: "#d8f7ed",
          200: "#b5eedf",
          300: "#78ddc8",
          400: "#34c4aa",
          500: "#18a68f",
          600: "#108673",
          700: "#106b5d",
          800: "#11554b",
          900: "#12463f"
        },
        signal: {
          amber: "#d68a00",
          red: "#d94f45",
          green: "#20a06b",
          violet: "#7d5bd1"
        }
      },
      fontSize: {
        xs: ["0.75rem", { lineHeight: "1rem" }],
        sm: ["0.875rem", { lineHeight: "1.25rem" }],
        base: ["1rem", { lineHeight: "1.5rem" }],
        lg: ["1.125rem", { lineHeight: "1.75rem" }],
        xl: ["1.25rem", { lineHeight: "1.75rem" }],
        "2xl": ["1.5rem", { lineHeight: "2rem" }]
      },
      borderRadius: {
        sm: "0.25rem",
        md: "0.375rem",
        lg: "0.5rem"
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"]
      }
    }
  },
  plugins: []
};

export default config;
