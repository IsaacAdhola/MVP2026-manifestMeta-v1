# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set environment variable to allow print statements to be displayed immediately
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

# Set the working directory in the container
WORKDIR /app

# Install build tools and other dependencies needed to compile Python packages
# (facebook_business, cryptography, grpc) on the slim image
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        build-essential \
        libffi-dev \
        libssl-dev \
        curl && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Do not bake secrets into the image; pass them at runtime with --env-file or compose
EXPOSE 8000

# Command to run the Slack / HTTP app
CMD ["sh", "-c", "uvicorn app:api --host 0.0.0.0 --port ${PORT:-8000}"]
