FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY ./src ./src
COPY ./config ./config

# Expose API port
EXPOSE 8000

# Run FastAPI server
CMD ["uvicorn", "src.inference.api:app", "--host", "0.0.0.0", "--port", "8000"]
