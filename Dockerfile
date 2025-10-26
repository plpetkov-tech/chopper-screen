FROM alpine:3.20

# Build arguments for versioning
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=latest

# Labels for better container metadata
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.authors="plpetkov-tech" \
      org.opencontainers.image.url="https://github.com/plpetkov-tech/chopper-screen" \
      org.opencontainers.image.source="https://github.com/plpetkov-tech/chopper-screen" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.title="Chopper Screen Dashboard" \
      org.opencontainers.image.description="Web content display dashboard for framebuffer devices"

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-pygame \
    chromium \
    chromium-chromedriver \
    xvfb \
    ttf-freefont \
    mesa-dri-gallium \
    libdrm \
    && rm -rf /var/cache/apk/*

# Create app directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application
COPY dashboard.py .

# Environment variables with defaults
ENV DISPLAY_URL="https://google.com" \
    REFRESH_INTERVAL="300" \
    NIGHT_MODE_ENABLED="true" \
    NIGHT_START="22:00" \
    NIGHT_END="07:00" \
    WINDOW_WIDTH="800" \
    WINDOW_HEIGHT="600" \
    CHROMIUM_TIMEOUT="30" \
    CHECK_INTERVAL="60" \
    FULLSCREEN="true"
# SDL_VIDEODRIVER - Auto-detected (kmsdrm, fbcon, directfb). Override if needed.

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f dashboard.py || exit 1

# Run as non-root where possible (note: framebuffer access may require root)
# RUN adduser -D -u 1000 dashboard
# USER dashboard

CMD ["python3", "-u", "dashboard.py"]
