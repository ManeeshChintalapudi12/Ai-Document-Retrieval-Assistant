import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}", "./lib/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#07111f",
          900: "#0c1728",
          800: "#12203a",
        },
        mist: {
          50: "#f7f8fb",
          100: "#eef2f8",
          200: "#dce6f2",
        },
        accent: {
          50: "#eefbf9",
          500: "#0f766e",
          600: "#0b5f58",
        },
        warning: {
          50: "#fff5f5",
          100: "#ffe5e5",
          600: "#dc2626",
          700: "#b91c1c",
        },
      },
      boxShadow: {
        soft: "0 18px 50px rgba(6, 15, 32, 0.18)",
      },
      backgroundImage: {
        "mesh-gradient":
          "radial-gradient(circle at top left, rgba(15, 118, 110, 0.18), transparent 30%), radial-gradient(circle at top right, rgba(59, 130, 246, 0.16), transparent 28%), linear-gradient(180deg, #07111f 0%, #0c1728 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
