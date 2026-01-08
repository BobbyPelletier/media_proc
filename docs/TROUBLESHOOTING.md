# MediaMTX Stream Manager - Troubleshooting Guide

This guide covers common issues and their solutions.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Container Issues](#container-issues)
3. [Stream Issues](#stream-issues)
4. [Playback Issues](#playback-issues)
5. [Recording Issues](#recording-issues)
6. [Hardware Acceleration Issues](#hardware-acceleration-issues)
7. [Network Issues](#network-issues)
8. [Performance Issues](#performance-issues)

---

## Installation Issues

### Docker Compose Version Errors

**Problem**: Error about docker-compose.yml version compatibility

**Solution**:
```bash
# Update docker-compose
sudo apt update
sudo apt install docker-compose-plugin

# Or use docker compose (without hyphen)
docker compose up -d
```

### Permission Denied Errors

**Problem**: Cannot create directories or access files

**Solution**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, then test
docker ps

# Fix directory permissions
sudo chown -R $USER:$USER ./media ./recordings ./logs
```

### Port Already in Use

**Problem**: Error binding to port (5000, 8554, etc.)

**Solution**:
```bash
# Find what's using the port
sudo lsof -i :5000

# Kill the process or change port in .env
WEB_PORT=5001

# Restart services
docker-compose down
docker-compose up -d
```

---

## Container Issues

### Containers Won't Start

**Problem**: Services fail to start or immediately exit

**Diagnosis**:
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs stream_manager
docker-compose logs mediamtx

# Check for errors
docker-compose logs --tail=50
```

**Solutions**:

1. **Missing .env file**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Invalid configuration**:
   ```bash
   # Validate docker-compose.yml
   docker-compose config
   ```

3. **Network conflicts**:
   ```bash
   # Remove old networks
   docker network prune

   # Recreate
   docker-compose down
   docker-compose up -d
   ```

### Container Crashes Immediately

**Problem**: Container starts then exits

**Solution**:
```bash
# Check exit reason
docker-compose logs stream_manager

# Common causes:
# - Missing mediamtx.yml: Verify file exists
# - Python errors: Check app.py syntax
# - Missing dependencies: Rebuild image
docker-compose build --no-cache stream_manager
```

### Cannot Connect to MediaMTX

**Problem**: stream_manager can't reach mediamtx

**Solution**:
```bash
# Check both containers are on same network
docker network inspect media_proc_media_network

# Test connectivity from stream_manager
docker exec stream_manager ping mediamtx
docker exec stream_manager curl http://mediamtx:9997/v3/config

# Restart both services
docker-compose restart
```

---

## Stream Issues

### Stream Won't Start

**Problem**: Clicking "Start Stream" fails or shows error

**Diagnosis**:
```bash
# Check stream_manager logs
docker-compose logs -f stream_manager

# Look for FFmpeg errors
docker exec stream_manager ps aux | grep ffmpeg
```

**Solutions**:

1. **File Not Found**:
   - Verify file path in /media
   - Check file permissions (readable by container)
   - Ensure file is a valid video format

2. **MediaMTX Not Ready**:
   ```bash
   # Check MediaMTX is running
   docker-compose ps mediamtx

   # Check API accessibility
   curl http://localhost:9997/v3/config
   ```

3. **FFmpeg Encoding Error**:
   - Try software encoding (disable hardware acceleration)
   - Check video file is not corrupted
   - Verify resolution/bitrate settings are reasonable

4. **Stream Name Conflict**:
   - Use a unique stream name
   - Stop existing stream with same name first

### Stream Starts But Stops Immediately

**Problem**: Stream appears in UI then disappears

**Diagnosis**:
```bash
# Watch logs in real-time
docker-compose logs -f stream_manager

# Check for FFmpeg errors
docker exec stream_manager ps aux
```

**Solutions**:

1. **Source File Issues**:
   - File may be corrupted
   - Unsupported codec
   - Try re-encoding the source file

2. **Hardware Acceleration Failed**:
   - Disable hardware acceleration
   - Verify GPU is accessible to container
   - Check drivers are installed

3. **MediaMTX Connection Lost**:
   - Check MediaMTX logs
   - Verify network connectivity
   - Restart MediaMTX

### Stream Shows "Error" Status

**Problem**: Stream card shows red error status

**What This Means**: FFmpeg process has terminated unexpectedly

**Actions**:
```bash
# Check logs for the specific stream
docker-compose logs stream_manager | grep "stream_name"

# Common causes:
# - Source file removed/moved
# - MediaMTX crashed
# - Encoding error
# - Out of memory
```

**Solutions**:
- Check source file still exists
- Verify sufficient disk space
- Reduce bitrate or resolution
- Try different hardware acceleration option

---

## Playback Issues

### Cannot View Stream in VLC/Player

**Problem**: RTSP URL doesn't work in VLC or other players

**Diagnosis**:
```bash
# Test RTSP URL
ffplay rtsp://your-server:8554/stream_name

# Or with VLC from command line
vlc rtsp://your-server:8554/stream_name

# Check MediaMTX logs
docker-compose logs mediamtx
```

**Solutions**:

1. **Firewall Blocking Ports**:
   ```bash
   # Check firewall rules
   sudo ufw status

   # Allow streaming ports
   sudo ufw allow 8554/tcp  # RTSP
   sudo ufw allow 1935/tcp  # RTMP
   sudo ufw allow 8888/tcp  # HLS
   sudo ufw allow 8889/tcp  # WebRTC
   sudo ufw allow 8890/udp  # SRT
   ```

2. **Wrong URL**:
   - Verify stream name matches exactly
   - Check protocol and port are correct
   - Try IP address instead of hostname

3. **Authentication Required**:
   ```bash
   # Include credentials in URL
   rtsp://username:password@server:8554/stream_name
   ```

4. **Network Connectivity**:
   ```bash
   # Test port accessibility
   telnet your-server 8554

   # Or with nc
   nc -zv your-server 8554
   ```

### WebRTC Won't Connect

**Problem**: WebRTC viewer shows connection error

**Solutions**:

1. **SERVER_HOST Misconfigured**:
   - Edit .env: `SERVER_HOST=your-public-ip`
   - Must be IP or domain accessible from viewer
   - Restart containers after changing

2. **NAT/Firewall Issues**:
   - Open UDP port 8189 for WebRTC
   - Configure TURN server if behind strict NAT
   - Check mediamtx.yml webrtcAdditionalHosts

3. **Browser Compatibility**:
   - Use Chrome, Firefox, or Safari (latest versions)
   - Check browser console for errors
   - Try different browser

### HLS Playback Stutters/Buffers

**Problem**: HLS stream is choppy or constantly buffering

**Solutions**:

1. **Bitrate Too High**:
   - Reduce stream bitrate in configuration
   - Use lower resolution
   - Check viewer's network speed

2. **Segment Duration**:
   - Edit mediamtx.yml:
     ```yaml
     hlsSegmentDuration: 2s  # Increase for less segments
     hlsPartDuration: 500ms   # Increase for smoother playback
     ```

3. **Server Resources**:
   - Check CPU usage: `docker stats`
   - Enable hardware acceleration
   - Reduce concurrent streams

---

## Recording Issues

### Recordings Not Saving

**Problem**: Recording enabled but no files in /recordings

**Diagnosis**:
```bash
# Check recordings directory
ls -lh recordings/

# Check MediaMTX logs for recording errors
docker-compose logs mediamtx | grep -i record

# Verify recording is enabled for path
curl http://localhost:9997/v3/config/paths/get/stream_name
```

**Solutions**:

1. **Directory Permissions**:
   ```bash
   # Check ownership
   ls -ld recordings/

   # Fix permissions
   chmod -R 755 recordings/
   sudo chown -R $USER:$USER recordings/
   ```

2. **Disk Space Full**:
   ```bash
   # Check available space
   df -h

   # Clean old recordings
   find recordings/ -type f -mtime +30 -delete
   ```

3. **Recording Not Enabled**:
   - Verify "Enable Recording" was checked in UI
   - Stop and restart stream with recording enabled

### Cannot Download Recordings

**Problem**: Download button doesn't work

**Solutions**:

1. **File Permissions**:
   ```bash
   # Make recordings readable
   chmod -R 644 recordings/**/*.mp4
   ```

2. **Browser Blocking**:
   - Check browser's download settings
   - Disable popup blocker
   - Try different browser

3. **Large File Size**:
   - Download may take time, wait for browser
   - For very large files, use direct download:
     ```bash
     scp user@server:/path/to/recordings/file.mp4 ./
     ```

### Recording Files Corrupted

**Problem**: Recordings won't play or are incomplete

**Causes**:
- Stream stopped abruptly (power loss, crash)
- Disk full during recording
- Hardware failure

**Solutions**:

1. **Attempt Repair**:
   ```bash
   # Use FFmpeg to repair MP4
   ffmpeg -i corrupted.mp4 -c copy repaired.mp4
   ```

2. **Prevention**:
   - Use UPS for power backup
   - Monitor disk space regularly
   - Enable filesystem journaling

---

## Hardware Acceleration Issues

### NVENC Not Working

**Problem**: NVENC encoding fails or not available

**Diagnosis**:
```bash
# Check NVIDIA driver on host
nvidia-smi

# Check nvidia-docker is installed
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Check GPU accessible in container
docker exec stream_manager nvidia-smi
```

**Solutions**:

1. **Install nvidia-docker2**:
   ```bash
   # Add NVIDIA Docker repository
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
     sudo tee /etc/apt/sources.list.d/nvidia-docker.list

   # Install nvidia-docker2
   sudo apt update
   sudo apt install nvidia-docker2

   # Restart Docker
   sudo systemctl restart docker
   ```

2. **Enable GPU in docker-compose.yml**:
   ```yaml
   stream_manager:
     runtime: nvidia
     environment:
       - NVIDIA_VISIBLE_DEVICES=all
   ```

3. **Driver Too Old**:
   - Update NVIDIA drivers on host
   - Requires driver version 450+ for newer GPUs

### QuickSync Not Working

**Problem**: QSV encoding fails

**Diagnosis**:
```bash
# Check /dev/dri exists
ls -l /dev/dri/

# Check accessible in container
docker exec stream_manager ls -l /dev/dri/
```

**Solutions**:

1. **Add Device to Container**:
   ```yaml
   stream_manager:
     devices:
       - /dev/dri:/dev/dri
   ```

2. **Check CPU Supports QuickSync**:
   - Requires Intel 6th gen (Skylake) or newer
   - Check: https://ark.intel.com/

3. **Install Intel Media Driver**:
   ```bash
   # On host
   sudo apt install intel-media-va-driver
   ```

### VA-API Fails

**Problem**: VA-API encoding errors

**Solutions**:

1. **Install VA-API Drivers**:
   ```bash
   # For AMD
   sudo apt install mesa-va-drivers

   # For Intel
   sudo apt install intel-media-va-driver
   ```

2. **Check Device Permissions**:
   ```bash
   # Add user to render group
   sudo usermod -aG render $USER
   ```

---

## Network Issues

### Cannot Access Web UI

**Problem**: http://server:5000 times out or refuses connection

**Solutions**:

1. **Check Container Running**:
   ```bash
   docker-compose ps stream_manager
   ```

2. **Check Port Forwarding**:
   ```bash
   # Verify port is listening
   sudo netstat -tlnp | grep 5000

   # Or with ss
   sudo ss -tlnp | grep 5000
   ```

3. **Firewall Rules**:
   ```bash
   # Allow web port
   sudo ufw allow 5000/tcp
   ```

4. **Try Localhost**:
   ```bash
   # From server itself
   curl http://localhost:5000
   ```

### Viewers Can't Access Streams

**Problem**: Users can view web UI but not streams

**Solutions**:

1. **Open Streaming Ports**:
   ```bash
   sudo ufw allow 8554/tcp  # RTSP
   sudo ufw allow 1935/tcp  # RTMP
   sudo ufw allow 8888/tcp  # HLS
   sudo ufw allow 8889/tcp  # WebRTC
   sudo ufw allow 8189/udp  # WebRTC
   sudo ufw allow 8890/udp  # SRT
   ```

2. **Port Forwarding (if behind router)**:
   - Forward ports in router configuration
   - Map external ports to internal ports

3. **Use Public IP**:
   - Don't use 127.0.0.1 or localhost in stream URLs
   - Use server's public IP or domain

---

## Performance Issues

### High CPU Usage

**Problem**: Server CPU maxed out

**Solutions**:

1. **Enable Hardware Acceleration**:
   - Use NVENC, QSV, or VA-API
   - Can reduce CPU by 80-90%

2. **Reduce Stream Count**:
   - Limit concurrent streams
   - Stop unnecessary streams

3. **Lower Encoding Settings**:
   - Reduce bitrate
   - Lower resolution
   - Use faster preset

### High Memory Usage

**Problem**: Server running out of RAM

**Solutions**:

1. **Limit Container Memory**:
   ```yaml
   stream_manager:
     mem_limit: 2g
     mem_reservation: 1g
   ```

2. **Reduce Concurrent Streams**:
   - Each stream uses ~50-100MB

3. **Check for Memory Leaks**:
   ```bash
   # Monitor memory over time
   docker stats stream_manager

   # Restart if needed
   docker-compose restart stream_manager
   ```

### Disk I/O Bottleneck

**Problem**: Recordings stuttering, high disk wait

**Solutions**:

1. **Use Faster Storage**:
   - Move recordings to SSD
   - Use RAID for better I/O

2. **Reduce Recording Quality**:
   - Lower bitrate reduces disk writes
   - Stop recording unnecessary streams

3. **Monitor Disk Usage**:
   ```bash
   # Check I/O wait
   iostat -x 1

   # Check disk usage
   df -h
   ```

---

## Getting More Help

### Collecting Debug Information

When asking for help, provide:

1. **Docker Compose Logs**:
   ```bash
   docker-compose logs > debug.log
   ```

2. **Container Status**:
   ```bash
   docker-compose ps
   ```

3. **System Information**:
   ```bash
   docker version
   docker-compose version
   uname -a
   ```

4. **Configuration** (sanitized):
   - docker-compose.yml (remove sensitive info)
   - .env (remove passwords)
   - mediamtx.yml (remove credentials)

### Useful Commands

```bash
# View real-time logs
docker-compose logs -f

# Restart specific service
docker-compose restart stream_manager

# Rebuild and restart
docker-compose up -d --build

# Access container shell
docker exec -it stream_manager bash

# Check resource usage
docker stats

# Clean up unused resources
docker system prune -a
```

### Resources

- MediaMTX Documentation: https://github.com/bluenviron/mediamtx
- FFmpeg Documentation: https://ffmpeg.org/documentation.html
- Docker Documentation: https://docs.docker.com/
- Flask Documentation: https://flask.palletsprojects.com/
