#!/bin/bash
#
# Build and Push MediaMTX Stream Manager to Docker Hub
#
# Usage:
#   ./build-and-push.sh <dockerhub-username> [version]
#
# Example:
#   ./build-and-push.sh myusername 1.1.0
#   ./build-and-push.sh myusername        # defaults to 'latest'
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Get Docker Hub username
DOCKERHUB_USERNAME=$1
VERSION=${2:-latest}

if [ -z "$DOCKERHUB_USERNAME" ]; then
    echo -e "${RED}Error: Docker Hub username is required${NC}"
    echo "Usage: $0 <dockerhub-username> [version]"
    echo "Example: $0 myusername 1.1.0"
    exit 1
fi

IMAGE_NAME="$DOCKERHUB_USERNAME/mediamtx-stream-manager"
IMAGE_TAG="$IMAGE_NAME:$VERSION"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}MediaMTX Stream Manager - Docker Build${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Image Name: $IMAGE_TAG"
echo "Also tagging as: $IMAGE_NAME:latest"
echo ""

# Check if logged into Docker Hub
echo -e "${YELLOW}Checking Docker Hub authentication...${NC}"
if ! docker info | grep -q "Username"; then
    echo -e "${YELLOW}Not logged into Docker Hub. Please login:${NC}"
    docker login
fi

# Build the image
echo ""
echo -e "${YELLOW}Building Docker image...${NC}"
cd web
docker build -t "$IMAGE_TAG" -t "$IMAGE_NAME:latest" .
cd ..

echo -e "${GREEN}✓ Build complete${NC}"

# Ask for confirmation before pushing
echo ""
echo -e "${YELLOW}Ready to push to Docker Hub:${NC}"
echo "  - $IMAGE_TAG"
if [ "$VERSION" != "latest" ]; then
    echo "  - $IMAGE_NAME:latest"
fi
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Push cancelled${NC}"
    exit 0
fi

# Push to Docker Hub
echo ""
echo -e "${YELLOW}Pushing to Docker Hub...${NC}"
docker push "$IMAGE_TAG"

if [ "$VERSION" != "latest" ]; then
    docker push "$IMAGE_NAME:latest"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Successfully pushed to Docker Hub${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Your image is now available at:"
echo "  docker pull $IMAGE_TAG"
echo ""
echo "To use in docker-compose.yml, replace:"
echo "  YOUR_DOCKERHUB_USERNAME with: $DOCKERHUB_USERNAME"
echo ""
