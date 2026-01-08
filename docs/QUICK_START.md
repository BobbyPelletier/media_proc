# MediaMTX Stream Manager - Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Linux server (Ubuntu/Debian recommended)
- Docker and Docker Compose installed
- Video files to stream (optional - can use IP cameras)

## Installation Steps

### 1. Copy Files

```bash
# Copy the entire media_proc_final directory to your server
scp -r media_proc_final user@your-server:~/
ssh user@your-server
cd ~/media_proc_final
```

### 2. Configure Environment

```bash
# Create .env from template
cp .env.example .env

# Edit with your settings
nano .env
```

**Required Settings**:
```bash
SERVER_HOST=192.168.1.100  # Your server IP or domain
MEDIA_PATH=/path/to/videos # Where your video files are
RECORDINGS_PATH=./recordings
```

### 3. Run Setup Script

```bash
# Make executable
chmod +x setup.sh

# Run setup
./setup.sh
```

The script will:
- Check dependencies
- Create directories
- Build Docker images
- Start services

### 4. Access Web UI

Open browser to: `http://your-server:5000`

## First Stream

### From Video File

1. Click **Add New Stream**
2. Enter stream name (e.g., "test")
3. Select **Select from Server**
4. Choose a video file
5. Keep default settings
6. Click **Start Stream**

### From IP Camera

1. Click **Add New Stream**
2. Enter stream name (e.g., "camera1")
3. Select **IP Camera**
4. Enter RTSP URL: `rtsp://user:pass@camera-ip:554/stream`
5. Configure bitrate/resolution as needed
6. Click **Start Stream**

## View Your Stream

After starting, your stream is available at:

- **RTSP**: `rtsp://your-server:8554/test`
- **HLS**: `http://your-server:8888/test/index.m3u8`
- **WebRTC**: `http://your-server:8889/test`

### Test with VLC

```bash
vlc rtsp://your-server:8554/test
```

## Common Tasks

### Stop a Stream

Click the **Stop** button on the stream card

### Record a Stream

1. When creating stream, check **Enable Recording**
2. Recordings saved to `/recordings/streamname/`
3. View recordings via **Recordings** button

### Stop All Streams

Click **Stop All Streams** button

### Enable Hardware Acceleration

1. When creating stream, select **Hardware Acceleration**:
   - **NVIDIA NVENC** (if you have NVIDIA GPU)
   - **Intel QuickSync** (if you have Intel CPU 6th gen+)
   - **VA-API** (for AMD GPUs)
2. Requires setup (see README.md for details)

## Troubleshooting

### Stream Won't Start

```bash
# Check logs
docker-compose logs -f stream_manager

# Common fixes:
# 1. Verify video file exists and is accessible
# 2. Try software encoding (no hardware acceleration)
# 3. Check MediaMTX is running: docker-compose ps
```

### Can't View Stream

```bash
# Check firewall
sudo ufw allow 8554/tcp  # RTSP
sudo ufw allow 8888/tcp  # HLS

# Test locally first
vlc rtsp://localhost:8554/streamname
```

### Web UI Not Accessible

```bash
# Check container is running
docker-compose ps

# Check logs
docker-compose logs stream_manager

# Allow web port
sudo ufw allow 5000/tcp
```

## Useful Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Update images
docker-compose pull
docker-compose up -d

# Check resource usage
docker stats
```

## Firewall Configuration

Open these ports for full functionality:

```bash
sudo ufw allow 5000/tcp   # Web UI
sudo ufw allow 8554/tcp   # RTSP
sudo ufw allow 1935/tcp   # RTMP
sudo ufw allow 8888/tcp   # HLS
sudo ufw allow 8889/tcp   # WebRTC
sudo ufw allow 8189/udp   # WebRTC
sudo ufw allow 8890/udp   # SRT
```

## Default Ports

| Service | Protocol | Port | Purpose |
|---------|----------|------|---------|
| Web UI | HTTP | 5000 | Management interface |
| RTSP | TCP | 8554 | Stream output |
| RTMP | TCP | 1935 | Stream output |
| HLS | HTTP | 8888 | Stream output |
| WebRTC | HTTP/UDP | 8889/8189 | Stream output |
| SRT | UDP | 8890 | Stream output |

## Performance Tips

### For Best Performance

1. **Enable Hardware Acceleration**
   - Reduces CPU usage by 80-90%
   - Allows more concurrent streams

2. **Use RTSP Protocol**
   - Lowest latency
   - Best compatibility

3. **Optimize Bitrate**
   - 2 Mbps for 720p
   - 4-5 Mbps for 1080p
   - Higher = better quality but more bandwidth

### Resource Requirements

Per stream (1080p, software encoding):
- CPU: 1 core
- RAM: 50-100 MB
- Disk (recording): ~900 MB/hour at 2 Mbps

With hardware encoding:
- CPU: 0.1 core
- RAM: 50-100 MB
- GPU: Minimal

## Next Steps

- **Read full documentation**: See [README.md](README.md)
- **Learn about features**: See [FEATURES.md](FEATURES.md)
- **Understand architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Troubleshoot issues**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Security Recommendations

### For Production Use

1. **Use SSL with a Reverse Proxy**
   - Deploy nginx or Caddy with SSL certificates
   - Configure to proxy to port 5000

2. **Use Stream Authentication**
   - Enable in stream configuration
   - Set username/password

3. **Firewall Configuration**
   - Only open required ports
   - Use UFW or iptables

4. **Regular Updates**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

## Getting Help

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Review logs: `docker-compose logs`
- Check MediaMTX docs: https://github.com/bluenviron/mediamtx

## Example Configuration

### .env File
```bash
SERVER_HOST=192.168.1.100
MEDIA_PATH=/home/user/videos
RECORDINGS_PATH=/home/user/recordings
LOGS_PATH=./logs
WEB_PORT=5000
TRAEFIK_ENABLE=false
```

### Stream Configuration
- **Name**: live
- **Source**: Select from Server → video.mp4
- **Protocol**: RTSP
- **Bitrate**: 2 Mbps
- **Resolution**: Original
- **Hardware Accel**: NVENC (if available)
- **Recording**: Enabled

**Result**: Stream accessible at `rtsp://192.168.1.100:8554/live`

## Success!

You should now have:
- ✅ Web UI accessible
- ✅ At least one test stream running
- ✅ Stream viewable in VLC or browser
- ✅ Understanding of basic operations

**Enjoy streaming!**
