"""Main entry point for the MCP WordPress server package."""

import asyncio
from mcp_wordpress.server import main

if __name__ == "__main__":
    asyncio.run(main())