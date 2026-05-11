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
          subtle: "#E6FAFA",
          tertiary: "#7C3AED", // AI 피드백 전용 보라
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
          placeholder: "#9CA3AF",
          disabled: "#D1D5DB",
        },
        surface: {
          body: "#F9FAFB",
          card: "#FFFFFF",
          subtle: "#F3F4F6",
          border: "#E5E7EB",
          divider: "#F3F4F6",
        },
        pastel: {
          purple: "#FAF0FD",
          mint: "#F0FDFA",
          yellow: "#FFFBEB",
          blue: "#EFF6FF",
        },
        info: { DEFAULT: "#2563EB", bg: "#DBEAFE" },
        ok: { DEFAULT: "#10B981", bg: "#D1FAE5" },
        warn: { DEFAULT: "#F59E0B", bg: "#FEF3C7" },
        danger: { DEFAULT: "#EF4444", bg: "#FEE2E2" },
        // AI 피드백 severity 계열
        ai: {
          detected: "#8B5CF6",
          pii: "#DC2626",
          guideline: "#F59E0B",
          style: "#3B82F6",
          brain: "#7C3AED",
        },
      },
      fontSize: {
        caption: ["12px", { lineHeight: "18px", letterSpacing: "-0.005em" }],
        "body-sm": ["13px", { lineHeight: "20px", letterSpacing: "-0.005em" }],
        body: ["14px", { lineHeight: "22px" }],
        "body-lg": ["15px", { lineHeight: "25px", letterSpacing: "-0.01em" }],
        title: ["17px", { lineHeight: "26px", letterSpacing: "-0.01em", fontWeight: "600" }],
        heading: ["20px", { lineHeight: "29px", letterSpacing: "-0.015em", fontWeight: "700" }],
        display: ["24px", { lineHeight: "34px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "display-lg": ["32px", { lineHeight: "42px", letterSpacing: "-0.025em", fontWeight: "700" }],
      },
      transitionTimingFunction: {
        "out-quart": "cubic-bezier(0.25, 1, 0.5, 1)",
        "out-expo": "cubic-bezier(0.16, 1, 0.3, 1)",
        standard: "cubic-bezier(0.2, 0, 0, 1)",
      },
      transitionDuration: {
        snap: "120ms",
        quick: "150ms",
        base: "200ms",
        moderate: "240ms",
        med: "320ms",
        slow: "480ms",
      },
      zIndex: {
        dropdown: "20",
        sticky: "30",
        overlay: "40",
        modal: "50",
        toast: "60",
        tooltip: "70",
        command: "80",
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
        slideIn: {
          from: { transform: "translateX(-16px)", opacity: "0" },
          to: { transform: "translateX(0)", opacity: "1" },
        },
        pulseSoft: {
          "0%,100%": { opacity: "1" },
          "50%": { opacity: "0.6" },
        },
        shake: {
          "0%,100%": { transform: "translateX(0)" },
          "25%,75%": { transform: "translateX(-3px)" },
          "50%": { transform: "translateX(3px)" },
        },
        sheen: {
          from: { backgroundPosition: "-200% 0" },
          to: { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "fade-in": "fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "slide-in": "slideIn 240ms cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "pulse-soft": "pulseSoft 1.6s ease-in-out infinite",
        shake: "shake 300ms ease-out",
        sheen: "sheen 1.5s ease-in-out",
      },
    },
  },
  plugins: [],
} satisfies Config;
