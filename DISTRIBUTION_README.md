# MediaMTX Stream Manager - Distribution Package

This is a ready-to-deploy distribution of the MediaMTX Stream Manager. This package has been sanitized and prepared for easy deployment on any server.

## Deployment Options

**Option 1: Docker Hub Image (Recommended)**
- Pull pre-built image from Docker Hub
- Faster deployment, no build required
- See `docs/DOCKER_HUB_GUIDE.md` for publishing instructions

**Option 2: Build Locally**
- Build the stream_manager image from source
- Useful for customization or offline deployment

This guide covers both options.

## What's Included

This distribution contains:
- Full Flask web application for stream management
- MediaMTX configuration for multi-protocol streaming
- Docker Compose setup for easy deployment
- Docker Hub build and push scripts
- Complete documentation

## Pre-Deployment Checklist

Before deploying, you must configure the following:

### 1. Docker Hub Username (If using Docker Hub image)

If using a Docker Hub image, edit `docker-compose.yml` and replace the image reference:
```yaml
stream_manager:
  image: YOUR_DOCKERHUB_USERNAME/mediamtx-stream-manager:latest
```

**To build locally instead**, comment out the `image:` line and uncomment `build: ./web`

### 2. Server IP Configuration

**Required for WebRTC support**

Edit `docker-compose.yml` and replace `YOUR_SERVER_IP` with your actual server IP:
```yaml
environment:
  - SERVER_IP=${SERVER_IP:-YOUR_SERVER_IP}  # Change YOUR_SERVER_IP
```

Edit `mediamtx.yml` and replace `YOUR_SERVER_IP`:
```yaml
webrtcAdditionalHosts: [YOUR_SERVER_IP]  # Change YOUR_SERVER_IP
```

### 3. Traefik Configuration (Optional)

If you're using Traefik reverse proxy:

1. Edit `docker-compose.yml`
2. Uncomment the `proxy` network under `stream_manager.networks`
3. Uncomment all Traefik labels
4. Replace `your-domain.com` with your actual domain
5. Uncomment the `proxy` network definition at the bottom

### 4. Hardware Acceleration (Optional)

If you have GPU hardware:

**For NVIDIA GPUs:**
```yaml
# Uncomment in docker-compose.yml:
runtime: nvidia
environment:
  - NVIDIA_VISIBLE_DEVICES=all
  - NVIDIA_DRIVER_CAPABILITIES=compute,video,utility
```

**For Intel QuickSync / VA-API:**
```yaml
# Uncomment in docker-compose.yml:
devices:
  - /dev/dri:/dev/dri
```

## Quick Deployment

### 1. Copy Files to Server

```bash
# On your server
mkdir -p ~/docker/media_proc
cd ~/docker

# Copy all files from this distribution to the server
scp -r media_proc_distribution/* user@server:~/docker/media_proc/
```

### 2. Create Required Directories

```bash
cd ~/docker/media_proc
mkdir -p media streams recordings logs hls
```

### 3. Configure (Required)

```bash
# Edit docker-compose.yml - Set SERVER_IP
nano docker-compose.yml

# Edit mediamtx.yml - Set webrtcAdditionalHosts
nano mediamtx.yml
```

### 4. Deploy

```bash
# Start services
docker-compose up -d

# Check logs
docker-compose logs -f

# Verify containers are running
docker-compose ps
```

### 5. Access Web UI

Open browser to:
- `http://YOUR_SERVER_IP:5000`

Or if using Traefik:
- `https://your-domain.com`

## First-Time Setup

1. **Add Video Files**: Place video files in the `media/` directory
2. **Create First Stream**:
   - Click "Add New Stream"
   - Enter stream name (e.g., "live")
   - Select video source
   - Configure settings (defaults work well)
   - Click "Start Stream"
3. **Test Stream**: Use the provided URLs to test in VLC or other player

## Stream URLs

After creating a stream named "mystream", access it at:

- **RTSP**: `rtsp://YOUR_SERVER_IP:8554/mystream`
- **RTMP**: `rtmp://YOUR_SERVER_IP:1935/mystream`
- **HLS**: `http://YOUR_SERVER_IP:8888/mystream`
- **WebRTC**: `http://YOUR_SERVER_IP:8889/mystream` (requires webrtcAdditionalHosts configured)
- **SRT**: `srt://YOUR_SERVER_IP:8890?streamid=publish:mystream`

## Audio Codec Selection

When creating streams, you can choose the audio codec in Advanced Options:

- **Opus** (Recommended): Required for WebRTC, excellent quality
- **AAC**: Better compatibility with some RTSP/RTMP players

**Note**: MediaMTX provides all output formats regardless of the publishing protocol. The protocol setting only affects how FFmpeg publishes to MediaMTX.

## Port Requirements

Ensure these ports are accessible:

| Port | Protocol | Purpose |
|------|----------|---------|
| 5000 | TCP | Web UI |
| 8554 | TCP | RTSP |
| 1935 | TCP | RTMP |
| 8888 | TCP | HLS |
| 8889 | TCP | WebRTC HTTP |
| 8189 | UDP | WebRTC UDP |
| 8890 | UDP | SRT |

## Environment Variables

You can override defaults by creating a `.env` file:

```bash
# .env file
SERVER_IP=192.168.1.100
WEB_PORT=5000
MEDIA_PATH=/path/to/videos
RECORDINGS_PATH=/path/to/recordings
LOGS_PATH=/path/to/logs
```

## Updating

```bash
# Pull latest MediaMTX image
docker-compose pull mediamtx

# Rebuild stream_manager if code changed
docker-compose up -d --build stream_manager

# Or restart everything
docker-compose down && docker-compose up -d
```

## Troubleshooting

### Containers Won't Start
```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs stream_manager
docker-compose logs mediamtx
```

### WebRTC Not Working
- Verify `webrtcAdditionalHosts` in `mediamtx.yml` is set correctly
- Ensure UDP port 8189 is open
- Use Opus audio codec (check Advanced Options when creating stream)

### Can't Access Web UI
- Verify port 5000 is open in firewall
- Check container is running: `docker-compose ps`
- Try accessing directly: `http://SERVER_IP:5000`

### Streams Won't Start
- Check FFmpeg errors in stream_manager logs
- Try without hardware acceleration first
- Verify video file path is correct
- Ensure file is readable by Docker container

## Getting Help

For detailed documentation, see:
- `README.md` - Complete user guide
- `docs/FEATURES.md` - Feature overview and technical details
- `docs/TROUBLESHOOTING.md` - Common issues and solutions
- `docs/ARCHITECTURE.md` - Technical architecture details
- `docs/QUICK_START.md` - Alternative quick setup guide

## Security Notes

- Change default passwords if you enable stream authentication
- Use Traefik/nginx with SSL for production deployments
- Restrict port access via firewall
- Don't expose MediaMTX API port (9997) to the internet
- Regularly update Docker images

## Credits

Built with:
- [MediaMTX](https://github.com/bluenviron/mediamtx) - Universal media server
- [FFmpeg](https://ffmpeg.org/) - Video encoding
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Docker](https://www.docker.com/) - Containerization

## License

This project uses:
- MediaMTX - MIT License
- FFmpeg - LGPL/GPL (depending on build)
- Flask - BSD License
