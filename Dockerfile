# Use official Python image as a slim base
FROM python:3.10-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies in a virtual environment
COPY requirements.txt ./
RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Expose port for uvicorn
EXPOSE 8000

# Use a non-root user for security (optional, can be commented out if issues)
# RUN useradd -m appuser && chown -R appuser /app
# USER appuser

# Start the FastAPI app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 