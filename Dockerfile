FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_wordpress/ ./mcp_wordpress/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY __main__.py .
COPY create_user.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash mcpuser
RUN chown -R mcpuser:mcpuser /app
USER mcpuser

# Set Python path
ENV PYTHONPATH=/app

# Default command runs the MCP server with stdio transport
CMD ["python", "-m", "mcp_wordpress.server"]