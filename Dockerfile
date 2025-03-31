# Generated by https://smithery.ai. See: https://smithery.ai/docs/config#dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirement and project files
COPY requirements.txt ./
COPY pyproject.toml ./
COPY README.md ./
COPY pubtator_server.py ./
COPY pubtator_search.py ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port if needed (not specified in MCP, but default is stdio)

# Command to run the MCP server
CMD ["python", "pubtator_server.py"]