# Docker Hub Publishing Guide

This guide explains how to publish the MediaMTX Stream Manager image to Docker Hub and how users can deploy it.

## For Maintainers: Publishing to Docker Hub

### Prerequisites

1. Docker Hub account (create at https://hub.docker.com)
2. Docker installed and running locally
3. Command line access

### Steps to Publish

#### 1. Login to Docker Hub

```bash
docker login
# Enter your Docker Hub username and password
```

#### 2. Build and Push (Automated Script)

Use the provided script for easy building and pushing:

```bash
# Basic usage - pushes as 'latest'
./build-and-push.sh YOUR_DOCKERHUB_USERNAME

# With version tag
./build-and-push.sh YOUR_DOCKERHUB_USERNAME 1.1.0
```

The script will:
- Build the image from the `web/` directory
- Tag it with both the specified version and 'latest'
- Push to Docker Hub
- Provide confirmation prompts

#### 3. Manual Build and Push (Alternative)

If you prefer manual control:

```bash
# Navigate to the web directory
cd web

# Build the image
docker build -t YOUR_DOCKERHUB_USERNAME/mediamtx-stream-manager:1.1.0 .
docker build -t YOUR_DOCKERHUB_USERNAME/mediamtx-stream-manager:latest .

# Push to Docker Hub
docker push YOUR_DOCKERHUB_USERNAME/mediamtx-stream-manager:1.1.0
docker push YOUR_DOCKERHUB_USERNAME/mediamtx-stream-manager:latest
```

#### 4. Update docker-compose.yml

After publishing, update the docker-compose.yml to reference your image:

```yaml
stream_manager:
  image: YOUR_DOCKERHUB_USERNAME/mediamtx-stream-manager:latest
```

### Best Practices for Publishing

1. **Version Tagging**: Always tag releases with semantic versioning (e.g., 1.1.0, 1.2.0)
2. **Latest Tag**: Keep the 'latest' tag updated with the most recent stable version
3. **Testing**: Test the built image locally before pushing to Docker Hub
4. **Documentation**: Update CHANGELOG.md with each release
5. **Size Optimization**: The current image is ~150MB (Python + FFmpeg). Consider multi-stage builds for smaller sizes if needed.

### Image Tags Strategy

- `latest` - Most recent stable release
- `1.1.0`, `1.2.0`, etc. - Specific version tags
- `dev` (optional) - Development/testing versions

## For Users: Deploying from Docker Hub

Once the image is published to Docker Hub, users can deploy it easily:

### Quick Start with Docker Hub Image

#### 1. Create Project Directory

```bash
mkdir -p ~/docker/media_proc
cd ~/docker/media_proc
```

#### 2. Download Configuration Files

Users need these files from the distribution:
- `docker-compose.yml`
- `mediamtx.yml`
- `.env.example` (optional)

#### 3. Configure

Edit `docker-compose.yml`:
```yaml
stream_manager:
  image: YOUR_DOCKERHUB_USERNAME/mediamtx-stream-manager:latest
```

Edit `mediamtx.yml`:
```yaml
webrtcAdditionalHosts: [YOUR_SERVER_IP]
```

Set `SERVER_IP` environment variable in docker-compose.yml or .env file.

#### 4. Deploy

```bash
# Pull and start services
docker-compose up -d

# View logs
docker-compose logs -f stream_manager

# Access at http://YOUR_SERVER_IP:5000
```

### Advantages of Using Docker Hub Image

✅ **No Build Required**: Users don't need to build the image locally
✅ **Faster Deployment**: Just pull the pre-built image
✅ **Consistent**: Everyone uses the same tested image
✅ **Easier Updates**: Just pull the latest image and restart
✅ **Smaller Download**: Only configuration files needed initially

### Updating to New Version

```bash
# Pull latest image
docker-compose pull stream_manager

# Restart with new image
docker-compose up -d stream_manager

# Or restart everything
docker-compose down && docker-compose up -d
```

## Docker Hub Repository Setup

### Recommended Repository Description

```
MediaMTX Stream Manager - Web-based management interface for MediaMTX streaming server

A Flask application that provides an easy-to-use web UI for managing multi-protocol video streams 
(RTSP, RTMP, SRT, HLS, WebRTC) with MediaMTX.

Features:
• Multiple video sources (files, IP cameras, uploads)
• Audio codec selection (Opus/AAC)
• Hardware acceleration support
• Stream recording and management
• Dark mode UI
• Docker Compose deployment

Documentation: https://github.com/YOUR_USERNAME/YOUR_REPO
```

### Repository Tags

Add these tags to your Docker Hub repository for discoverability:
- mediamtx
- streaming
- rtsp
- rtmp
- webrtc
- hls
- srt
- video-streaming
- flask
- ffmpeg
- stream-manager

### README for Docker Hub

Create a README.md on Docker Hub with quick start instructions:

```markdown
# MediaMTX Stream Manager

Web-based management interface for MediaMTX multi-protocol streaming.

## Quick Start

1. Create docker-compose.yml and mediamtx.yml (see documentation)
2. Configure SERVER_IP in docker-compose.yml
3. Run: `docker-compose up -d`
4. Access: http://YOUR_SERVER_IP:5000

## Documentation

Full documentation: [GitHub Repository Link]

## Environment Variables

- `SERVER_IP` - Server IP for WebRTC (required)
- `MEDIAMTX_HOST` - MediaMTX hostname (default: mediamtx)
- `WEB_PORT` - Web UI port (default: 5000)

## Volumes

- `/streams` - Stream configuration files
- `/media` - Video source files
- `/recordings` - Stream recordings

## Tags

- `latest` - Most recent stable release
- `1.1.0` - Specific version

## License

MIT License - See repository for details
```

## Troubleshooting

### Build Fails

**Issue**: Docker build fails with dependency errors

**Solution**: Ensure all files in `web/` directory are present:
- app.py
- Dockerfile
- requirements.txt
- templates/
- static/

### Push Permission Denied

**Issue**: Cannot push to Docker Hub

**Solution**: 
1. Verify you're logged in: `docker login`
2. Check repository name matches your username
3. Ensure repository exists on Docker Hub or is public

### Image Too Large

**Issue**: Image size is too large (>500MB)

**Solution**: Current image is ~150MB which is reasonable. If needed:
1. Use Alpine base image instead of Python slim
2. Implement multi-stage builds
3. Remove unnecessary dependencies

### Users Can't Pull Image

**Issue**: Users get "permission denied" or "not found" errors

**Solution**:
1. Verify repository is public on Docker Hub
2. Check image name is correct: `username/mediamtx-stream-manager:latest`
3. Ensure image was successfully pushed

## CI/CD Integration (Optional)

For automated builds on GitHub:

```yaml
# .github/workflows/docker-publish.yml
name: Docker Publish

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Login to Docker Hub
        uses: docker/login-action@v1
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Build and push
        uses: docker/build-push-action@v2
        with:
          context: ./web
          push: true
          tags: |
            ${{ secrets.DOCKERHUB_USERNAME }}/mediamtx-stream-manager:latest
            ${{ secrets.DOCKERHUB_USERNAME }}/mediamtx-stream-manager:${{ github.ref_name }}
```

## Support

For issues or questions:
- GitHub Issues: [Your Repository]
- Documentation: [Link to full docs]
- Docker Hub: [Link to Docker Hub repository]
