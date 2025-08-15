/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  env: {
    NEXT_PUBLIC_MCP_SERVER_URL: process.env.MCP_SERVER_URL || 'http://localhost:8000',
    NEXT_PUBLIC_MCP_SSE_PATH: process.env.MCP_SSE_PATH || '/sse',
  },
};

module.exports = nextConfig;