# Use a base image with necessary build tools
FROM python:3.11-slim AS builder

# Accept host user/group IDs to set correct ownership on output
ARG USER_ID=1000
ARG GROUP_ID=1000

# Install required packages for building
RUN apt-get update && apt-get install -y \
    gcc \
    musl-dev \
    build-essential \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the application code
COPY . .

# Install PyInstaller
RUN pip install pyinstaller
RUN pip install -r requirements.txt

# Create a binary with PyInstaller
RUN pyinstaller --onefile --clean quadlet_compose.py

# Create /result dir in case it is not mounted
RUN mkdir -p /result

# Export binary with host user ownership
RUN cp /app/dist/quadlet_compose /result/quadlet-compose \
    && chown ${USER_ID}:${GROUP_ID} /result/quadlet-compose