# MediaMTX Stream Manager - Architecture Documentation

## System Overview

The MediaMTX Stream Manager is a containerized application stack that provides web-based management for video streaming. It bridges user-friendly configuration with powerful streaming capabilities through FFmpeg and MediaMTX.

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Browser                         │
│                    (Web UI / JavaScript)                     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   Stream Manager (Flask)                     │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Web UI     │  │  REST API    │  │  FFmpeg Manager  │  │
│  │  (Flask)    │  │  (Endpoints) │  │  (Threading)     │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
│         │                 │                    │             │
│         └─────────────────┴────────────────────┘             │
│                           │                                  │
│                  ┌────────┴─────────┐                       │
│                  │  Process Manager  │                       │
│                  │  (Thread Safe)    │                       │
│                  └────────┬─────────┘                        │
└───────────────────────────┼──────────────────────────────────┘
                            │
                    FFmpeg Processes
                    (Encoding)
                            │
                            ↓ RTSP/RTMP/SRT
┌─────────────────────────────────────────────────────────────┐
│                      MediaMTX Server                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   RTSP   │  │   RTMP   │  │   HLS    │  │  WebRTC  │   │
│  │  :8554   │  │  :1935   │  │  :8888   │  │  :8889   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────────────────────────────────┐   │
│  │   SRT    │  │        Control API                    │   │
│  │  :8890   │  │          :9997                        │   │
│  └──────────┘  └──────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ↓ Stream Output
                   ┌──────────────┐
                   │   Viewers    │
                   │  (Players)   │
                   └──────────────┘
```

## Service Components

### 1. Stream Manager (Flask Application)

**Purpose**: Web interface and stream lifecycle management

**Responsibilities**:
- Serve web UI (HTML/CSS/JavaScript)
- Handle REST API requests
- Manage FFmpeg encoding processes
- Configure MediaMTX paths via Control API
- Persist stream configuration
- Handle file uploads and browsing
- Manage recordings

**Technology Stack**:
- Python 3.11
- Flask 3.0.0 (web framework)
- subprocess module (process management)
- threading module (concurrent operations)
- requests library (MediaMTX API client)

**Key Files**:
- `app.py` - Main Flask application (REST API endpoints)
- `templates/index.html` - Web UI structure
- `static/js/app.js` - Frontend JavaScript
- `static/css/style.css` - UI styling
- `streams_config.json` - Persistent stream configuration

**Ports**:
- 5000 - Web UI and REST API

### 2. MediaMTX Server

**Purpose**: Multi-protocol streaming server

**Responsibilities**:
- Accept incoming streams (RTSP/RTMP/SRT)
- Transcode and distribute to multiple protocols
- Handle viewer connections
- Provide low-latency HLS
- Manage WebRTC connections
- Record streams to disk
- Expose metrics and control API

**Technology Stack**:
- MediaMTX v1.9+ (Go-based streaming server)
- FFmpeg (built-in for transcoding)

**Key Files**:
- `mediamtx.yml` - Server configuration

**Ports**:
- 8554 - RTSP server
- 1935 - RTMP server
- 8888 - HLS server
- 8889 - WebRTC server
- 8890 - SRT server
- 9997 - Control API
- 9998 - Metrics API

## Data Flow

### Stream Creation Flow

1. **User Input** → Web UI form submission
2. **Frontend Validation** → JavaScript validates required fields
3. **API Request** → POST to `/api/start` with configuration
4. **Backend Processing**:
   - Validate stream name uniqueness
   - Process file upload (if applicable)
   - Generate FFmpeg command with encoding parameters
   - Configure MediaMTX path via Control API (if recording enabled)
   - Start FFmpeg subprocess
   - Store configuration in `streams_config.json`
   - Add to active streams tracking
5. **Response** → Success/error message to frontend
6. **UI Update** → Display new stream card with metrics

### Stream Monitoring Flow

1. **Periodic Polling** → Frontend JavaScript polls `/api/streams` every 2 seconds
2. **Backend Aggregation**:
   - Check FFmpeg process status
   - Query MediaMTX API for viewer count and bitrate
   - Compile health status
3. **Response** → JSON with stream details
4. **UI Update** → Update stream cards with current metrics

### Stream Stopping Flow

1. **User Action** → Click stop button
2. **API Request** → POST to `/api/stop` with stream name
3. **Backend Processing**:
   - Terminate FFmpeg process gracefully
   - Remove from active streams
   - Update `streams_config.json`
4. **Response** → Success confirmation
5. **UI Update** → Remove stream card

## Storage Architecture

### Volumes and Persistence

```
Host Filesystem          Container Mount
─────────────────        ───────────────
./media/          →      /media          (video files)
./recordings/     →      /recordings     (recorded streams)
./logs/           →      /logs           (application logs)
./web/            →      /app            (stream_manager code)
./hls/            →      /hls            (HLS segments)
```

### File Organization

**Media Files** (`/media`):
- User video files for streaming
- Uploaded files stored here
- Supports: MP4, MKV, AVI, MOV, FLV, TS, WebM

**Recordings** (`/recordings`):
- Organized by stream name: `/recordings/{stream_name}/`
- Filename format: `YYYY-MM-DD_HH-MM-SS-microseconds.mp4`
- Written directly by MediaMTX during streaming

**Logs** (`/logs`):
- `mediamtx.log` - MediaMTX server logs
- Docker logs via `docker-compose logs`

**Configuration** (`/app`):
- `streams_config.json` - Persisted stream configurations
- Enables auto-restart on container restart

## Process Management

### FFmpeg Process Lifecycle

The stream manager spawns FFmpeg as subprocesses:

```python
# Process creation
process = subprocess.Popen(
    ffmpeg_command,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    preexec_fn=os.setsid  # Create new process group
)

# Process tracking
active_streams[stream_name] = {
    'process': process,
    'config': {...},
    'start_time': timestamp
}

# Process termination
os.killpg(os.getpgid(process.pid), signal.SIGTERM)
```

### Thread Safety

Multiple users can manage streams simultaneously. Thread safety is ensured with:

```python
active_streams_lock = threading.Lock()

with active_streams_lock:
    # Critical section - modify active_streams
    active_streams[name] = {...}
```

### Process Health Monitoring

Each API call checks process status:

```python
if process.poll() is not None:
    # Process has terminated
    status = 'error'
```

## Network Architecture

### Docker Networking

All containers run on a custom bridge network:

```yaml
networks:
  media_network:
    driver: bridge
```

**Benefits**:
- Service discovery by container name
- Isolated from host network
- Inter-container communication without port mapping

**Container Communication**:
- `stream_manager` → `mediamtx:9997` (Control API)
- `stream_manager` → `mediamtx:8554` (RTSP publishing)

### Port Exposure

Only necessary ports are exposed to host:

- **5000** - Web UI
- **8554** - RTSP (for viewers)
- **1935** - RTMP (for viewers)
- **8888** - HLS (for viewers)
- **8889** - WebRTC (for viewers)
- **8890** - SRT (for viewers)

Internal ports (9997, 9998) remain container-only.

## Security Architecture

### Authentication Layers

1. **Web UI**: No built-in authentication (use reverse proxy basic auth or external auth)
2. **Stream Publishing**: MediaMTX configured to allow from Docker network
3. **Stream Playback**: Public by default, optional per-stream authentication
4. **MediaMTX Control API**: IP-restricted to Docker network

### MediaMTX Authentication

```yaml
authInternalUsers:
  - user: any
    ips: ['127.0.0.1', '::1', '172.30.0.0/16']
    permissions:
      - action: publish  # Allow from Docker network
  - user: any
    ips: []
    permissions:
      - action: playback  # Allow from anywhere
```

### Per-Stream Authentication

When enabled in UI:
- FFmpeg publishes with credentials: `rtsp://user:pass@mediamtx:8554/stream`
- MediaMTX enforces authentication for that path
- Viewers must provide credentials

### Network Security

- Docker network isolation
- Firewall recommended for production
- Use reverse proxy (nginx/Caddy) with SSL for production
- No sensitive data in containers (use environment variables)

## API Architecture

### REST Endpoints

**GET /api/streams**
- Returns: Array of active streams with status
- Used by: Frontend polling

**POST /api/start**
- Body: Stream configuration
- Returns: Success/error message
- Creates: FFmpeg process, MediaMTX path config

**POST /api/stop**
- Body: `{name: "stream"}`
- Returns: Success/error message
- Terminates: FFmpeg process

**GET /api/files**
- Query: `?path=/media/subfolder`
- Returns: Directory listing
- Used by: File browser modal

**POST /api/upload**
- Body: Multipart form with file
- Returns: Uploaded filename
- Stores: File in /media

**GET /api/recordings**
- Returns: Array of recording files with metadata
- Scans: /recordings directory recursively

**DELETE /api/recordings/<filename>**
- Deletes: Specific recording file
- Returns: Success/error

**GET /api/export-obs**
- Returns: OBS scene collection JSON
- Includes: All active streams as sources

### MediaMTX Control API

**GET http://mediamtx:9997/v3/paths/list**
- Returns: All configured paths
- Used by: Stream metrics

**PATCH http://mediamtx:9997/v3/config/paths/patch/{name}**
- Body: Path configuration
- Used by: Enable recording per stream

## Encoding Pipeline

### FFmpeg Command Construction

```bash
ffmpeg -re \
  -stream_loop -1 \          # Loop video file
  -i /media/video.mp4 \       # Input file
  -c:v h264_nvenc \           # Video codec (hw accel)
  -b:v 2M \                   # Bitrate
  -vf scale=1920:1080 \       # Resolution
  -c:a aac \                  # Audio codec
  -f rtsp \                   # Output format
  rtsp://mediamtx:8554/stream # Destination
```

### Hardware Acceleration Options

**NVIDIA NVENC**:
```bash
-c:v h264_nvenc -preset p4 -tune ll
```

**Intel QuickSync**:
```bash
-hwaccel qsv -c:v h264_qsv
```

**VA-API**:
```bash
-hwaccel vaapi -vaapi_device /dev/dri/renderD128 -c:v h264_vaapi
```

### Encoding Parameters

- **Bitrate**: 1-8 Mbps (user selectable)
- **Resolution**: Original or downscaled
- **Codec**: H.264 (hardware or software)
- **Audio**: AAC 128kbps
- **Format**: RTSP/RTMP/SRT (MediaMTX accepts all)

## Stream Persistence

### Configuration File

`streams_config.json` stores all stream configurations:

```json
{
  "stream1": {
    "name": "stream1",
    "file": "/media/video.mp4",
    "protocol": "rtsp",
    "bitrate": "2M",
    "resolution": "1920:1080",
    "hw_accel": "nvenc",
    "enable_recording": true,
    "auth_user": "user",
    "auth_pass": "pass"
  }
}
```

### Auto-Restart on Boot

On container startup:
1. Load `streams_config.json`
2. For each stored configuration:
   - Verify video file still exists
   - Reconstruct FFmpeg command
   - Start subprocess
   - Add to active_streams tracking

### Persistence Guarantees

- Configuration saved immediately after successful start
- Removed immediately after manual stop
- Survives container restarts
- Survives host reboots (if Docker starts on boot)

## Scalability Considerations

### Vertical Scaling

**CPU**:
- Software encoding: ~1 core per 1080p stream
- Hardware encoding: ~0.1 core per 1080p stream

**Memory**:
- ~50MB per active stream
- ~100MB base for MediaMTX

**Disk I/O**:
- Recording: Bitrate × number of streams
- 2Mbps stream = ~900MB/hour

**Network**:
- Outbound: Bitrate × number of viewers
- Load balancing recommended for >100 viewers

### Horizontal Scaling

For large deployments:
- Run multiple stream_manager instances
- Single MediaMTX cluster (origin/edge topology)
- Load balancer for web UI
- Shared network storage for media files

## Monitoring and Observability

### Available Metrics

**MediaMTX Metrics** (port 9998):
- Active connections
- Bitrate per path
- Packet loss
- Prometheus format

**Stream Manager**:
- Process status (via process.poll())
- Stream count
- Uptime per stream

### Logging

**Application Logs**:
```bash
docker-compose logs -f stream_manager
docker-compose logs -f mediamtx
```

**FFmpeg Logs**:
- Captured via subprocess STDOUT/STDERR
- Available in Docker logs

## Technology Choices and Rationale

### Why MediaMTX?

- **Multi-protocol support**: Single source, multiple outputs
- **Low latency**: Sub-second latency with WebRTC/HLS LL
- **Control API**: Dynamic configuration without restarts
- **Lightweight**: Minimal resource usage
- **Active development**: Regular updates and features

### Why Flask?

- **Simplicity**: Easy to understand and modify
- **Python ecosystem**: Rich libraries (subprocess, requests)
- **REST-friendly**: Natural API design
- **Lightweight**: Low overhead

### Why FFmpeg?

- **Universal support**: Handles all video formats
- **Hardware acceleration**: NVENC, QSV, VA-API
- **Flexible encoding**: Fine-grained parameter control
- **Reliable**: Battle-tested in production

### Why Docker?

- **Portability**: Run anywhere
- **Isolation**: Clean dependencies
- **Reproducibility**: Consistent deployments
- **Scalability**: Easy to orchestrate

## Future Architecture Considerations

### Potential Enhancements

1. **Database**: Replace JSON with PostgreSQL for better concurrency
2. **Message Queue**: Add Redis/RabbitMQ for async task processing
3. **Clustering**: MediaMTX origin/edge for geographic distribution
4. **Auth System**: Add proper user management
5. **Monitoring**: Integrate Prometheus + Grafana
6. **CDN Integration**: Automatic HLS push to CDN
7. **Webhooks**: Event notifications (stream start/stop/error)
8. **Scheduler**: Automated stream scheduling
