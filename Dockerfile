FROM python:3.10.11-slim

COPY . /src
WORKDIR /src

RUN apt-get update && apt-get -y install \
    libgl1-mesa-glx \
    libglib2.0-0 \
    build-essential \
    curl \
    pkg-config \
    libssl-dev \
    cmake \
    git \
    clang \
    libclang-dev \
    ffmpeg \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && . $HOME/.cargo/env \
    && rustup default stable \
    && rustup target add aarch64-unknown-linux-gnu

RUN /bin/sh -c pip install --upgrade pip && pip install -r requirements.txt