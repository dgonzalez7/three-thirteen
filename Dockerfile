# Stage 1: Use a slim Python image
FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non-root user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

# Install dependencies first (Docker caches this layer separately,
# so dependencies are only reinstalled when requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ app/

# Switch to non-root user
USER appuser

# Expose the port FastAPI will listen on
EXPOSE 8000

# Start the web server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]