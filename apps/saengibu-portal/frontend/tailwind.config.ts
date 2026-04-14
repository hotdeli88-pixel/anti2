import type { Config } from "tailwindcss";

export default {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#13C3C3",
          hover: "#0EA5A5",
          light: "#F0FDFA",
          50: "#F0FDFA",
          100: "#CCFBF1",
          500: "#13C3C3",
          600: "#0EA5A5",
          700: "#0D8F8F",
        },
        ink: {
          dark: "#1F2937",
          gray: "#6B7280",
          light: "#9CA3AF",
        },
        surface: {
          body: "#F9FAFB",
          card: "#FFFFFF",
          border: "#E5E7EB",
        },
        pastel: {
          purple: "#FAF0FD",
          mint: "#F0FDFA",
          yellow: "#FFFBEB",
        },
        warn: "#F59E0B",
        danger: "#EF4444",
        ok: "#10B981",
      },
      fontFamily: {
        sans: [
          "Pretendard Variable",
          "Pretendard",
          "-apple-system",
          "BlinkMacSystemFont",
          "system-ui",
          "Roboto",
          "Helvetica Neue",
          "Segoe UI",
          "Apple SD Gothic Neo",
          "Noto Sans KR",
          "sans-serif",
        ],
      },
      borderRadius: {
        md: "8px",
        lg: "12px",
        xl: "16px",
      },
      boxShadow: {
        sm: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        md: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
        hover: "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-out forwards",
      },
    },
  },
  plugins: [],
} satisfies Config;
