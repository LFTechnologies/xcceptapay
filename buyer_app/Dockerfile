FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    zip \
    unzip \
    openjdk-11-jdk \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    autoconf \
    automake \
    libtool \
    pkg-config \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libtinfo5 \
    cmake \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd -m -s /bin/bash user
USER user
WORKDIR /home/user

# Install buildozer
RUN pip3 install --user buildozer cython

# Set PATH
ENV PATH="/home/user/.local/bin:${PATH}"

# Create app directory
WORKDIR /home/user/app

# Copy app files
COPY --chown=user:user . .

# Build command
CMD ["buildozer", "-v", "android", "debug"]
