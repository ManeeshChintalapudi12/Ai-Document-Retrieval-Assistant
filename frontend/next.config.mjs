const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/chat",
        destination: `${apiBaseUrl}/chat`,
      },
    ];
  },
};

export default nextConfig;
