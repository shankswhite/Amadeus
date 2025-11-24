# Open Deep Research - Production Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (including Playwright dependencies)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package installer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copy project files
COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/
COPY langgraph.json ./

# Create empty tests directory (required by setup tools)
RUN mkdir -p tests && touch tests/__init__.py

# Install Python dependencies
RUN uv pip install --system .

# 🔧 FIXED: Copy修复后的文件（必须在pip install之后，避免被覆盖）
COPY searcrawl_client.py ./src/open_deep_research/
COPY utils_fixed.py ./src/open_deep_research/utils.py

# Install Playwright browsers (only Chromium for crawling)
RUN playwright install chromium
RUN playwright install-deps chromium

# Expose LangGraph server port
EXPOSE 8123

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8123/health || exit 1

# Start LangGraph server
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "8123"]

