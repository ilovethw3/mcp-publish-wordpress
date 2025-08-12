/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    // Proxy API requests to the MCP server
    return [
      {
        source: '/api/mcp/:path*',
        destination: process.env.MCP_SERVER_URL || 'http://localhost:8000/:path*',
      },
    ];
  },
  env: {
    MCP_SERVER_URL: process.env.MCP_SERVER_URL || 'http://localhost:8000',
    MCP_SSE_PATH: process.env.MCP_SSE_PATH || '/sse',
  },
};

module.exports = nextConfig;