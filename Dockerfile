# ================================================
# Speech Transcription & Medical Lab Report Service
# Dockerfile (Production-inspired)
# ================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies (OpenCV, PyMuPDF, audio libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies manifest
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app/ /app/app/
COPY Celloscope_Final_Project_Design_Specification.md /app/
COPY SYSTEM_ARCHITECTURE.md /app/
COPY README.md /app/

# Default environment variables for container (Mock providers by default)
ENV SPEECH_PROVIDER=mock \
    OCR_PROVIDER=mock \
    LOG_LEVEL=INFO \
    HOST=0.0.0.0 \
    PORT=8000

# Expose server port
EXPOSE 8000

# Healthcheck definition
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Command to launch FastAPI service with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
