# MediaMTX Stream Manager

[![Docker Pulls](https://img.shields.io/docker/pulls/YOUR_USERNAME/mediamtx-stream-manager)](https://hub.docker.com/r/YOUR_USERNAME/mediamtx-stream-manager)
[![Docker Image Size](https://img.shields.io/docker/image-size/YOUR_USERNAME/mediamtx-stream-manager/latest)](https://hub.docker.com/r/YOUR_USERNAME/mediamtx-stream-manager)

A web-based management interface for MediaMTX that enables easy multi-protocol streaming from video files, IP cameras, and other sources.

## Features

- 🎥 Multiple video sources (files, IP cameras, uploads)
- 🌐 Multi-protocol streaming (RTSP, RTMP, SRT, HLS, WebRTC)
- 🎵 Flexible audio codecs (Opus for WebRTC, AAC for compatibility)
- ⚡ Hardware acceleration (NVIDIA NVENC, Intel QuickSync, VA-API)
- 📹 Stream recording management
- 🔒 Stream authentication
- 🌓 Dark mode UI
- 📦 Docker Compose deployment

## Quick Start

### 1. Create docker-compose.yml

```yaml
version: '3.8'

services:
  mediamtx:
    image: bluenviron/mediamtx:latest
    container_name: mediamtx
    restart: unless-stopped
    ports:
      - "8554:8554"  # RTSP
      - "1935:1935"  # RTMP
      - "8888:8888"  # HLS
      - "8889:8889"  # WebRTC
      - "8890:8890/udp"  # SRT
    volumes:
      - ./mediamtx.yml:/mediamtx.yml
      - ./recordings:/recordings
    networks:
      - media_network

  stream_manager:
    image: YOUR_USERNAME/mediamtx-stream-manager:latest
    container_name: stream_manager
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - ./streams:/streams
      - ./media:/media
      - ./recordings:/recordings
    environment:
      - MEDIAMTX_HOST=mediamtx
      - SERVER_IP=YOUR_SERVER_IP  # Required for WebRTC
      - RTSP_PORT=8554
      - RTMP_PORT=1935
      - HLS_PORT=8888
      - WEBRTC_PORT=8889
      - SRT_PORT=8890
    networks:
      - media_network
    depends_on:
      - mediamtx

networks:
  media_network:
    driver: bridge
```

### 2. Create mediamtx.yml

Download the sample configuration from the [GitHub repository] or create a basic one:

```yaml
# Minimal MediaMTX configuration
webrtc: yes
webrtcAddress: :8889
webrtcAdditionalHosts: [YOUR_SERVER_IP]  # Replace with your server IP

recordPath: /recordings/%path/%Y-%m-%d_%H-%M-%S
recordFormat: fmp4
recordSegmentDuration: 1h
```

### 3. Deploy

```bash
# Create directories
mkdir -p streams media recordings

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Access web UI at http://YOUR_SERVER_IP:5000
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MEDIAMTX_HOST` | MediaMTX container hostname | `mediamtx` | No |
| `SERVER_IP` | Server IP for WebRTC | - | **Yes** |
| `RTSP_PORT` | RTSP port | `8554` | No |
| `RTMP_PORT` | RTMP port | `1935` | No |
| `HLS_PORT` | HLS port | `8888` | No |
| `WEBRTC_PORT` | WebRTC port | `8889` | No |
| `SRT_PORT` | SRT port | `8890` | No |

## Volumes

| Path | Description |
|------|-------------|
| `/app/streams` | Stream configuration files |
| `/app/media` | Video source files |
| `/app/recordings` | Stream recordings |

## Ports

| Port | Protocol | Service |
|------|----------|---------|
| 5000 | HTTP | Web UI |

## Usage

1. **Access Web UI**: Open `http://YOUR_SERVER_IP:5000`
2. **Create Stream**: Click "Add New Stream" and configure:
   - Stream name
   - Video source (file, upload, or IP camera)
   - Encoding options (bitrate, resolution)
   - Audio codec (Opus for WebRTC, AAC for RTSP/RTMP)
3. **View Stream**: Use the provided URLs for RTSP, RTMP, HLS, WebRTC, or SRT

### Stream URLs

After creating a stream named "mystream":
- **RTSP**: `rtsp://YOUR_SERVER_IP:8554/mystream`
- **RTMP**: `rtmp://YOUR_SERVER_IP:1935/mystream`
- **HLS**: `http://YOUR_SERVER_IP:8888/mystream`
- **WebRTC**: `http://YOUR_SERVER_IP:8889/mystream`
- **SRT**: `srt://YOUR_SERVER_IP:8890?streamid=publish:mystream`

## Hardware Acceleration

Add to docker-compose.yml for GPU encoding:

**NVIDIA NVENC:**
```yaml
stream_manager:
  runtime: nvidia
  environment:
    - NVIDIA_VISIBLE_DEVICES=all
    - NVIDIA_DRIVER_CAPABILITIES=compute,video,utility
```

**Intel QuickSync / VA-API:**
```yaml
stream_manager:
  devices:
    - /dev/dri:/dev/dri
```

## Documentation

- Full Documentation: [GitHub Repository Link]
- Features Guide: See docs/FEATURES.md
- Troubleshooting: See docs/TROUBLESHOOTING.md
- Architecture: See docs/ARCHITECTURE.md

## Updates

```bash
# Pull latest image
docker-compose pull stream_manager

# Restart with new version
docker-compose up -d stream_manager
```

## Version Tags

- `latest` - Most recent stable release
- `1.1.0` - Specific version tags

## Requirements

- Docker Engine 20.10+
- Docker Compose 1.29+
- 2GB RAM minimum (4GB recommended)
- FFmpeg (included in container)

## License

MIT License - See repository for full details

## Credits

Built with:
- [MediaMTX](https://github.com/bluenviron/mediamtx) - Universal media server
- [FFmpeg](https://ffmpeg.org/) - Video encoding
- [Flask](https://flask.palletsprojects.com/) - Web framework

## Support

- 📖 Documentation: [GitHub Repository]
- 🐛 Issues: [GitHub Issues]
- 💬 Discussions: [GitHub Discussions]
