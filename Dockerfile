# OpenMontage Container (GPU-enabled)
# Multi-stage build: Node deps + CUDA/Python + FFmpeg

FROM node:18-bookworm-slim AS node-deps
WORKDIR /app/remotion-composer
COPY remotion-composer/package.json remotion-composer/package-lock.json* ./
RUN npm install

# Use NVIDIA CUDA base with Python support
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.11, Node.js 18, FFmpeg, Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3.11-dev python3-pip \
    ffmpeg \
    curl \
    gnupg \
    chromium-browser \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Tell Puppeteer/Remotion to use system Chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV CHROME_PATH=/usr/bin/chromium-browser

# CUDA visibility
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

WORKDIR /app

# Python core deps
COPY requirements.txt requirements-gpu.txt ./
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt \
    && pip install --no-cache-dir --break-system-packages piper-tts || true

# PyTorch with CUDA 12.4 + GPU deps (diffusers, transformers, accelerate)
RUN pip install --no-cache-dir --break-system-packages \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124 \
    && pip install --no-cache-dir --break-system-packages \
    diffusers transformers accelerate

# Copy Node deps from first stage
COPY remotion-composer/package.json remotion-composer/
COPY --from=node-deps /app/remotion-composer/node_modules remotion-composer/node_modules

# Copy full project
COPY . .

# Create .env from example if not mounted
RUN cp -n .env.example .env 2>/dev/null || true

# Output directory
RUN mkdir -p /app/output /app/pipeline

VOLUME ["/app/output", "/app/pipeline"]

ENTRYPOINT ["/bin/bash"]
