import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17211d",
        paper: "#f6f7f4",
        line: "#d9ded8",
        pine: "#11645a",
        brass: "#b87816",
        signal: "#bc3f31"
      },
      boxShadow: {
        panel: "0 18px 45px rgba(23, 33, 29, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;
