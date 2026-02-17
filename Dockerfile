# AegisLM Dockerfile
# Multi-Agent Adversarial LLM Evaluation Framework
# Production-ready for HuggingFace Spaces

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 aegislm && \
    chown -R aegislm:aegislm /app

# Copy requirements first for better caching
COPY --chown=aegislm:aegislm requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=aegislm:aegislm . .

# Make startup script executable (it's in the repo as start.sh)
RUN chmod +x /app/start.sh

# Switch to non-root user
USER aegislm

# Expose both ports (8000 for API, 7860 for Dashboard/HF Spaces)
EXPOSE 7860 8000

# Health check - check dashboard on 7860
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/ || curl -f http://localhost:8000/ping || exit 1

# Run both services using the startup script
CMD ["/app/start.sh"]
