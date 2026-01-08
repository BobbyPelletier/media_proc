#!/bin/bash

# MediaMTX Stream Manager - Setup Script
# This script prepares the environment and starts the application

set -e  # Exit on error

echo "=========================================="
echo "MediaMTX Stream Manager - Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "$1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi
print_success "Docker is installed"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi
print_success "Docker Compose is installed"

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_success ".env file created"
        print_warning "Please edit .env file with your configuration before continuing!"
        echo ""
        echo "At minimum, set the following:"
        echo "  - SERVER_HOST (your server IP or domain)"
        echo "  - MEDIA_PATH (path to your video files)"
        echo ""
        read -p "Press Enter after you've configured .env, or Ctrl+C to exit..."
    else
        print_error ".env.example not found. Cannot create .env file."
        exit 1
    fi
else
    print_success ".env file exists"
fi

# Source .env file
export $(grep -v '^#' .env | xargs)

# Create required directories
print_info ""
print_info "Creating required directories..."

mkdir -p "${MEDIA_PATH:-./media}"
print_success "Created media directory: ${MEDIA_PATH:-./media}"

mkdir -p "${RECORDINGS_PATH:-./recordings}"
print_success "Created recordings directory: ${RECORDINGS_PATH:-./recordings}"

mkdir -p "${LOGS_PATH:-./logs}"
print_success "Created logs directory: ${LOGS_PATH:-./logs}"

mkdir -p ./hls
print_success "Created HLS directory: ./hls"

# Set permissions (optional, may require sudo)
print_info ""
print_info "Setting directory permissions..."
chmod -R 755 "${MEDIA_PATH:-./media}" 2>/dev/null || print_warning "Could not set permissions on media directory (may need sudo)"
chmod -R 755 "${RECORDINGS_PATH:-./recordings}" 2>/dev/null || print_warning "Could not set permissions on recordings directory (may need sudo)"
chmod -R 755 "${LOGS_PATH:-./logs}" 2>/dev/null || print_warning "Could not set permissions on logs directory (may need sudo)"

# Check for hardware acceleration
print_info ""
print_info "Checking for hardware acceleration support..."

# Check for NVIDIA GPU
if command -v nvidia-smi &> /dev/null; then
    print_success "NVIDIA GPU detected. You can use NVENC encoding."
    print_info "  Make sure nvidia-docker2 is installed for GPU support."
else
    print_info "  No NVIDIA GPU detected (or nvidia-smi not found)"
fi

# Check for Intel/AMD GPU
if [ -d /dev/dri ]; then
    print_success "/dev/dri device found. You can use QuickSync or VA-API encoding."
else
    print_info "  No /dev/dri device found"
fi

# Validate configuration
print_info ""
print_info "Validating configuration..."

if [ -z "$SERVER_HOST" ] || [ "$SERVER_HOST" = "localhost" ]; then
    print_warning "SERVER_HOST is set to localhost. WebRTC may not work for remote viewers."
    print_info "  Consider setting SERVER_HOST to your server's IP or domain in .env"
fi

# Pull Docker images
print_info ""
print_info "Pulling Docker images..."
docker-compose pull || print_error "Failed to pull Docker images"
print_success "Docker images pulled"

# Build custom images
print_info ""
print_info "Building stream_manager image..."
docker-compose build stream_manager || print_error "Failed to build stream_manager image"
print_success "stream_manager image built"

# Start services
print_info ""
print_info "Starting services..."
docker-compose up -d || print_error "Failed to start services"
print_success "Services started"

# Wait for services to be healthy
print_info ""
print_info "Waiting for services to be ready..."
sleep 5

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    print_success "Services are running"
else
    print_error "Some services failed to start. Check logs with: docker-compose logs"
    exit 1
fi

# Display access information
print_info ""
echo "=========================================="
print_success "Setup completed successfully!"
echo "=========================================="
echo ""
echo "Access the web UI at:"
echo "  http://${SERVER_HOST}:${WEB_PORT:-5000}"
echo ""
echo "Stream output ports:"
echo "  RTSP:   rtsp://${SERVER_HOST}:8554/<stream_name>"
echo "  RTMP:   rtmp://${SERVER_HOST}:1935/<stream_name>"
echo "  HLS:    http://${SERVER_HOST}:8888/<stream_name>/index.m3u8"
echo "  WebRTC: http://${SERVER_HOST}:8889/<stream_name>"
echo "  SRT:    srt://${SERVER_HOST}:8890?streamid=read:<stream_name>"
echo ""
echo "Useful commands:"
echo "  View logs:        docker-compose logs -f"
echo "  Stop services:    docker-compose down"
echo "  Restart services: docker-compose restart"
echo "  Update images:    docker-compose pull && docker-compose up -d"
echo ""
print_info "For more information, see README.md"
echo ""
