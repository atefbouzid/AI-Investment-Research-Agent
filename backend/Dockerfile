FROM python:3.11-slim

# Install system dependencies (build tools, LaTeX for pdflatex, and git for some pip packages)
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        build-essential \
        wget \
        curl \
        git \
        ca-certificates \
        texlive-latex-base \
        texlive-latex-extra \
        texlive-fonts-recommended \
        texlive-fonts-extra \
        texlive-latex-recommended \
        latexmk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage layer caching
COPY requirements.txt ./

# Create a venv (optional) and install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose API port
EXPOSE 8000

# Environment defaults (can be overridden by compose)
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Start the FastAPI app
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


