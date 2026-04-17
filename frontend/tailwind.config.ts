import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Trading candle palette
        candle: {
          green: "#22c55e",
          "green-bright": "#4ade80",
          "green-dark": "#15803d",
          red: "#ef4444",
          "red-bright": "#f87171",
          "red-dark": "#b91c1c",
        },
        // Arno's signature dark base
        void: "#03050a",
        dark: "#070b14",
        card: "#0d1628",
        // Text
        "text-primary": "#edf2f8",
        "text-secondary": "#b0bfce",
        "text-muted": "#7a8799",
        // Borders
        "border-subtle": "rgba(34, 197, 94, 0.15)",
        "border-hover": "rgba(34, 197, 94, 0.45)",
      },
      fontFamily: {
        heading: ["var(--font-space-grotesk)", "sans-serif"],
        body: ["var(--font-inter)", "sans-serif"],
      },
      backgroundImage: {
        "gradient-green":
          "linear-gradient(135deg, #22c55e 0%, #a7f3d0 45%, #22c55e 100%)",
        "gradient-red":
          "linear-gradient(135deg, #ef4444 0%, #fca5a5 45%, #ef4444 100%)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(32px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "shimmer-text": {
          "0%": { backgroundPosition: "0%" },
          "100%": { backgroundPosition: "200%" },
        },
        "orb-drift": {
          "0%": { transform: "translate(0, 0)" },
          "100%": { transform: "translate(40px, 30px)" },
        },
        "pulse-dot": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.15" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.9s ease both",
        "shimmer-text": "shimmer-text 4s linear infinite",
        "orb-drift": "orb-drift 18s ease-in-out infinite alternate",
        "pulse-dot": "pulse-dot 2.4s infinite",
      },
    },
  },
  plugins: [],
};

export default config;

