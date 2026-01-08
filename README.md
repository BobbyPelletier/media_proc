# MediaMTX Stream Manager

A web-based management interface for MediaMTX that enables easy streaming from video files, IP cameras, and other sources. Built with Flask, Docker, and MediaMTX for multi-protocol streaming support.

## Features

- **Multiple Source Types**: Stream from video files, IP cameras (RTSP), or upload new files
- **Multi-Protocol Support**: Automatically provides RTSP, RTMP, SRT, HLS, and WebRTC outputs
- **Flexible Audio Codec**: Choose between Opus (WebRTC-compatible) or AAC (RTSP/RTMP-compatible)
- **Hardware Acceleration**: Support for NVIDIA NVENC, Intel QuickSync, and VA-API encoding
- **Recording Management**: Record streams to disk and manage recordings through the web UI
- **Stream Authentication**: Password-protect individual streams
- **Stream Persistence**: Automatically restart streams after server reboot
- **OBS Integration**: Export stream configurations as OBS Studio scene collections
- **Bulk Operations**: Start, stop, and manage multiple streams simultaneously
- **Real-time Monitoring**: Live stream health metrics and status updates
- **File Browser**: Browse server filesystem to select video sources
- **Dark Mode**: Toggle between light and dark themes

## Architecture

The application consists of two main services orchestrated with Docker Compose:

1. **stream_manager** - Flask web application providing the management UI and REST API
2. **mediamtx** - MediaMTX server handling multi-protocol streaming

The stream manager uses FFmpeg to encode video sources and publish to MediaMTX, which then provides multiple output protocols for viewers.

## Prerequisites

- Docker and Docker Compose
- Linux host (tested on Ubuntu/Debian)
- Hardware encoding (optional but recommended):
  - NVIDIA GPU with NVENC support
  - Intel CPU with QuickSync support
  - AMD GPU with VA-API support

## Directory Structure

```
media_proc/
├── docker-compose.yml          # Container orchestration
├── web/                        # Flask application
│   ├── app.py                  # Backend API
│   ├── Dockerfile              # Container build instructions
│   ├── requirements.txt        # Python dependencies
│   ├── templates/              # HTML templates
│   │   └── index.html
│   └── static/                 # CSS and JavaScript
│       ├── css/style.css
│       └── js/app.js
├── mediamtx.yml               # MediaMTX configuration
├── streams/                   # Stream files directory
├── media/                     # Video files directory (user-provided)
├── recordings/                # Stream recordings directory
├── logs/                      # Application logs
├── README.md                  # This file
├── FEATURES.md               # Detailed feature documentation
└── TROUBLESHOOTING.md        # Common issues and solutions
```

## Quick Start

### 1. Clone and Configure

```bash
# Create deployment directory
mkdir -p ~/docker/media_proc
cd ~/docker/media_proc

# Copy all files from the media_proc directory
# (or clone from repository)

# Create required directories
mkdir -p media streams recordings logs hls
```

### 2. Configure Environment Variables

The application uses environment variables defined in `docker-compose.yml`. Key settings:

- **SERVER_IP**: Your server's IP address (required for WebRTC). Default: `YOUR_SERVER_IP`
- **WEB_PORT**: Web UI port. Default: `5000`
- **MEDIA_PATH**: Path to video files. Default: `./media`
- **RECORDINGS_PATH**: Path to recordings. Default: `./recordings`
- **LOGS_PATH**: Path to logs. Default: `./logs`

Edit these in `docker-compose.yml` or create a `.env` file:

```bash
# .env file example
SERVER_IP=192.168.1.100
WEB_PORT=5000
MEDIA_PATH=/path/to/video/files
RECORDINGS_PATH=/path/to/recordings
LOGS_PATH=/path/to/logs
```

### 3. Configure MediaMTX for WebRTC

Edit `mediamtx.yml` and replace `YOUR_SERVER_IP` with your server's IP:

```yaml
webrtcAdditionalHosts: [192.168.1.100]
```

### 4. Deploy with Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 5. Access the Web UI

Open your browser to:
- `http://your-server-ip:5000`

Or if using Traefik reverse proxy, configure the labels in `docker-compose.yml` (see Traefik Integration section below).

## Configuration

### MediaMTX Configuration

The `mediamtx.yml` file controls MediaMTX server behavior:

- **API Server**: Port 9997 for dynamic configuration
- **RTSP**: Port 8554 (TCP and UDP)
- **RTMP**: Port 1935
- **HLS**: Port 8888 with low-latency variant
- **WebRTC**: Port 8889 with STUN servers
- **SRT**: Port 8890

### Authentication

MediaMTX is configured to:
- Allow internal Docker network access without authentication
- Allow playback from any IP without authentication
- Require authentication for publishing (configured per-stream in UI)

### Hardware Acceleration

To use hardware encoding:

1. **NVIDIA NVENC**: Requires nvidia-docker2 runtime
   ```bash
   # Install nvidia-docker2
   sudo apt install nvidia-docker2
   sudo systemctl restart docker
   ```

2. **Intel QuickSync**: Requires `/dev/dri` device access
   ```bash
   # Already configured in docker-compose.yml
   ```

3. **VA-API (AMD/Intel)**: Requires `/dev/dri` device access
   ```bash
   # Already configured in docker-compose.yml
   ```

## Usage

### Creating a Stream

1. Click **Add New Stream** button
2. Enter a unique stream name (used in URLs)
3. Choose video source:
   - **Select from Server**: Browse existing files
   - **Upload File**: Upload a new video file
   - **IP Camera**: Enter RTSP URL
4. Configure encoding options (Basic):
   - Bitrate (1-8 Mbps)
   - Resolution (or keep original)
5. Configure advanced options (Optional):
   - Publishing Protocol (RTSP, SRT, or RTMP)
   - Audio Codec (Opus for WebRTC, AAC for RTSP/RTMP)
   - Hardware Acceleration (NVIDIA NVENC, Intel QuickSync, VA-API)
6. Enable recording (optional)
7. Enable authentication (optional)
8. Click **Start Stream**

### Viewing Streams

After creating a stream named "mystream", it's available at:

- **RTSP**: `rtsp://your-server:8554/mystream`
- **RTMP**: `rtmp://your-server:1935/mystream`
- **HLS**: `http://your-server:8888/mystream`
- **WebRTC**: `http://your-server:8889/mystream`
- **SRT**: `srt://your-server:8890?streamid=publish:mystream`

### Managing Recordings

1. Click **Recordings** button to view all recordings
2. Download recordings as needed
3. Delete old recordings to free space

### OBS Integration

1. Create multiple streams in the web UI
2. Click **Export OBS Scene** button
3. Import the downloaded JSON file in OBS Studio:
   - Scene Collection → Import
   - Select the downloaded file

### Bulk Operations

1. Select multiple streams using checkboxes
2. Click **Stop Selected** to stop all selected streams
3. Or use **Stop All Streams** to stop everything

## Troubleshooting

### Streams Won't Start

- Check logs: `docker-compose logs stream_manager`
- Verify video file exists and is readable
- Check FFmpeg encoding with hardware acceleration
- Try software encoding first (no hw_accel selected)

### Can't View Streams

- Verify MediaMTX is running: `docker-compose ps`
- Check firewall allows ports 8554, 1935, 8888, 8889, 8890
- For WebRTC, ensure `SERVER_HOST` in .env is correct
- Test RTSP with VLC: `vlc rtsp://your-server:8554/streamname`

### Recording Not Working

- Check recordings directory permissions
- Verify disk space available
- Check MediaMTX logs: `docker-compose logs mediamtx`

### Container Issues

```bash
# View logs
docker-compose logs -f stream_manager
docker-compose logs -f mediamtx

# Restart services
docker-compose restart

# Rebuild after changes
docker-compose up -d --build
```

## API Documentation

The Flask backend provides a REST API:

### GET /api/streams
Returns list of active streams with status and metrics.

### POST /api/start
Start a new stream.

**Body**:
```json
{
  "name": "stream1",
  "file": "/path/to/video.mp4",
  "protocol": "rtsp",
  "bitrate": "2M",
  "resolution": "1920:1080",
  "hw_accel": "nvenc",
  "enable_recording": true,
  "auth_user": "username",
  "auth_pass": "password"
}
```

### POST /api/stop
Stop a running stream.

**Body**:
```json
{
  "name": "stream1"
}
```

### GET /api/recordings
List all recordings with metadata.

### DELETE /api/recordings/<filename>
Delete a specific recording file.

## Traefik Integration

To use Traefik reverse proxy for HTTPS access:

1. Ensure you have a Traefik container running with the `proxy` network
2. Edit `docker-compose.yml` and uncomment:
   - The `proxy` network under `stream_manager.networks`
   - All Traefik labels, replacing `your-domain.com` with your actual domain
   - The `proxy` network definition at the bottom
3. Restart the container: `docker-compose up -d`

Example Traefik configuration:
```yaml
networks:
  - media_network
  - proxy  # Uncomment this

labels:
  - "traefik.enable=true"
  - "traefik.http.routers.stream-manager.rule=Host(`stream.yourdomain.com`)"
  - "traefik.http.routers.stream-manager.entrypoints=websecure"
  - "traefik.http.routers.stream-manager.tls=true"
```

## Security Considerations

- Change default MediaMTX API port if exposed to internet
- Use stream authentication for sensitive content
- Configure firewall to restrict access to streaming ports
- Use a reverse proxy (Traefik/nginx/Caddy) with SSL for encrypted web UI access
- Regularly update Docker images for security patches
- When exposing to the internet, restrict MediaMTX ports and only expose through secure protocols

## Performance Tips

- Use hardware acceleration when available (reduces CPU by 80%+)
- Adjust bitrate based on network capacity
- Use RTSP protocol for lowest latency
- Monitor disk space when recording is enabled
- Limit concurrent streams based on hardware capacity

## Maintenance

### Backup

Important files to backup:
- `streams_config.json` - Stream persistence configuration
- `recordings/` - All stream recordings
- `.env` - Environment configuration

### Updates

```bash
# Pull latest images
docker-compose pull

# Restart with new images
docker-compose up -d

# Rebuild stream_manager after code changes
docker-compose up -d --build stream_manager
```

### Logs

```bash
# View real-time logs
docker-compose logs -f

# View specific service
docker-compose logs -f stream_manager

# Save logs to file
docker-compose logs > debug.log
```

## Support

For issues and feature requests:
- Check the TROUBLESHOOTING.md file
- Review application logs
- Consult MediaMTX documentation: https://github.com/bluenviron/mediamtx

## License

This project uses:
- MediaMTX - MIT License
- FFmpeg - LGPL/GPL (depending on build)
- Flask - BSD License

## Credits

Built with:
- [MediaMTX](https://github.com/bluenviron/mediamtx) - Universal media server
- [FFmpeg](https://ffmpeg.org/) - Video encoding
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Docker](https://www.docker.com/) - Containerization
