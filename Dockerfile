# LangChain Agent with Kapa MCP Server Example
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source code is mounted as a volume (see docker-compose.yml)
# This allows editing files without rebuilding the container

# Set Python to run unbuffered for real-time output
ENV PYTHONUNBUFFERED=1

# Default to bash shell for interactive use
CMD ["/bin/bash"]

