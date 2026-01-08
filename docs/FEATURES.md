# MediaMTX Stream Manager - Features Documentation

## Overview

This document provides detailed information about all features available in the MediaMTX Stream Manager.

## Table of Contents

1. [Stream Sources](#stream-sources)
2. [Stream Configuration](#stream-configuration)
3. [Recording Management](#recording-management)
4. [Stream Authentication](#stream-authentication)
5. [Hardware Acceleration](#hardware-acceleration)
6. [Multi-Protocol Output](#multi-protocol-output)
7. [Stream Persistence](#stream-persistence)
8. [OBS Studio Integration](#obs-studio-integration)
9. [Bulk Operations](#bulk-operations)
10. [File Management](#file-management)
11. [Real-Time Monitoring](#real-time-monitoring)
12. [User Interface](#user-interface)

---

## Stream Sources

The application supports three types of video sources:

### 1. Server Files

**Description**: Stream from video files already on the server

**Supported Formats**:
- MP4 (H.264/H.265)
- MKV (Matroska)
- AVI
- MOV (QuickTime)
- FLV (Flash Video)
- TS (MPEG Transport Stream)
- WebM

**Usage**:
1. Select "Select from Server" radio button
2. Choose file from dropdown, or
3. Click "Browse Server" to navigate filesystem
4. Select file and click "Start Stream"

**Features**:
- File browser with breadcrumb navigation
- Displays file sizes and types
- Filters video files automatically
- Supports nested directories

**Technical Details**:
- FFmpeg loops video files automatically (`-stream_loop -1`)
- Original video transcoded to H.264
- Audio codec varies by protocol:
  - RTSP/RTMP: AAC (best compatibility)
  - SRT: Opus (modern, high quality)
- Playback rate synchronized to real-time (`-re` flag)

### 2. File Upload

**Description**: Upload video files from your computer to the server

**Upload Limits**:
- Maximum file size: 10GB (configurable)
- Supported formats: Same as server files
- Progress indicator during upload

**Usage**:
1. Select "Upload File" radio button
2. Click file input to browse local files
3. Select video file
4. Wait for upload to complete
5. Configure stream settings
6. Click "Start Stream"

**Features**:
- Real-time upload progress bar
- Percentage completion indicator
- Automatic retry on network errors
- Files stored in `/media` directory

**Technical Details**:
- Multipart form upload via JavaScript FormData
- Chunked transfer encoding for large files
- Files stored with sanitized filenames
- Automatic cleanup of failed uploads

### 3. IP Camera (RTSP)

**Description**: Stream from IP cameras or other RTSP sources

**Supported Protocols**:
- RTSP (primary)
- RTSP over TCP
- RTSP over HTTP

**Usage**:
1. Select "IP Camera" radio button
2. Enter RTSP URL: `rtsp://username:password@ip:port/path`
3. Configure encoding settings
4. Click "Start Stream"

**Common Camera URLs**:

**Hikvision**:
```
rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101
```

**Dahua**:
```
rtsp://admin:password@192.168.1.100:554/cam/realmonitor?channel=1&subtype=0
```

**Amcrest**:
```
rtsp://admin:password@192.168.1.100:554/cam/realmonitor?channel=1&subtype=1
```

**Reolink**:
```
rtsp://admin:password@192.168.1.100:554/h264Preview_01_main
```

**Technical Details**:
- FFmpeg connects as RTSP client
- Transcodes camera stream to configured settings
- Supports authentication in URL
- Handles connection drops with automatic reconnect

---

## Stream Configuration

### Stream Naming

**Format**: Alphanumeric with underscores/hyphens
**Examples**: `live`, `stream1`, `front_camera`, `test-stream`

**Requirements**:
- Must be unique
- Used in streaming URLs
- Cannot be changed after creation

**Best Practices**:
- Use descriptive names (`lobby_camera` vs `stream1`)
- Avoid spaces and special characters
- Keep names short for cleaner URLs

### Publishing Protocol

Choose how FFmpeg publishes to MediaMTX:

#### RTSP (Recommended)

**Best For**: General streaming, low latency
**Port**: 8554
**Latency**: <1 second
**Benefits**:
- Lowest overhead
- Most compatible
- Built-in to MediaMTX

**Use When**:
- Standard video streaming
- Local network streaming
- Security camera feeds

#### RTMP

**Best For**: Legacy compatibility, CDN integration
**Port**: 1935
**Latency**: 3-5 seconds
**Benefits**:
- Wide platform support
- Compatible with YouTube/Twitch ingest
- Stable protocol

**Use When**:
- Integrating with RTMP-based services
- CDN requires RTMP input
- Using legacy streaming tools

#### SRT (Secure Reliable Transport)

**Best For**: Internet streaming, poor networks
**Port**: 8890
**Latency**: 1-2 seconds
**Benefits**:
- Error correction
- Encryption built-in
- Handles packet loss well

**Use When**:
- Streaming over internet
- Unreliable network conditions
- Security is paramount

### Bitrate Configuration

**Options**: 1, 2, 3, 4, 5, 8 Mbps

**Guidelines by Resolution**:
- **360p**: 1 Mbps
- **480p**: 2 Mbps
- **720p**: 3-4 Mbps
- **1080p**: 5-8 Mbps
- **4K**: 15+ Mbps (custom FFmpeg command required)

**Considerations**:
- Higher bitrate = better quality + more bandwidth
- Consider viewer network capacity
- Balance quality vs. server resources
- Hardware acceleration enables higher bitrates

### Resolution Scaling

**Options**:
- Original (no scaling)
- 1080p (1920x1080)
- 720p (1280x720)
- 480p (854x480)
- 360p (640x360)

**Use Cases**:
- **Original**: Preserve source quality, sufficient bandwidth
- **1080p**: High quality for modern displays
- **720p**: Good balance of quality and bandwidth
- **480p**: Mobile viewers, bandwidth-limited
- **360p**: Very slow connections, bandwidth-critical

**Technical Notes**:
- Scaling uses FFmpeg's high-quality Lanczos algorithm
- Maintains aspect ratio automatically
- Upscaling not recommended (quality loss)

---

## Recording Management

### Enabling Recording

**Per-Stream Setting**: Toggle "Enable Recording" checkbox

**Storage Location**: `/recordings/{stream_name}/`

**Filename Format**: `YYYY-MM-DD_HH-MM-SS-microseconds`
**Example**: `2024-01-15_14-30-45-123456`
**Note**: Files are stored in fMP4 format (fragmented MP4)

### Recording Features

**Automatic Management**:
- Recordings start immediately when stream starts
- Recordings stop when stream stops
- Each stream session creates new file

**Format**:
- Container: fMP4 (fragmented MP4)
- Video Codec: H.264
- Audio Codec: Protocol-dependent (AAC for RTSP/RTMP, Opus for SRT)
- Segmented: New file every restart

### Recordings Browser

Access via "Recordings" button in main UI.

**Features**:
- List all recordings across all streams
- Grouped by stream name
- Shows file size and date
- Download individual recordings
- Delete recordings to free space
- Total storage usage displayed

**Operations**:

**Download Recording**:
1. Click "Recordings" button
2. Find desired recording
3. Click download icon
4. File downloads to browser

**Delete Recording**:
1. Click "Recordings" button
2. Find recording to delete
3. Click delete icon
4. Confirm deletion
5. File permanently removed

**Technical Details**:
- MediaMTX handles recording directly (no FFmpeg involvement)
- Recordings saved as stream is received
- No CPU overhead for recording
- Disk I/O matches stream bitrate

### Storage Management

**Recommendations**:
- Monitor disk usage regularly
- Delete old recordings proactively
- Consider external storage for long-term retention
- Automate cleanup with cron jobs

**Disk Usage Calculation**:
```
Recording Size = Bitrate × Duration
Example: 2 Mbps × 1 hour = 900 MB
```

---

## Stream Authentication

### Purpose

Protect streams from unauthorized viewers by requiring username/password.

### Configuration

**Per-Stream Setting**: Toggle "Enable Stream Authentication"

**Credentials**:
- Username: Alphanumeric, no spaces
- Password: Any characters (recommend strong password)

**Scope**: Applies to all protocols for that stream

### Publishing Authentication

When authentication enabled:
- FFmpeg publishes with credentials embedded in URL
- MediaMTX validates credentials before accepting stream
- Configuration stored in MediaMTX via Control API

### Playback Authentication

Viewers must provide credentials:

**RTSP**:
```
rtsp://username:password@server:8554/streamname
```

**RTMP**:
```
rtmp://server:1935/streamname?username=user&password=pass
```

**HLS**:
```
http://server:8888/streamname/index.m3u8?user=username&pass=password
```

**WebRTC**: Credentials prompted by browser

### Security Considerations

**Strengths**:
- Prevents casual unauthorized access
- Different credentials per stream
- No authentication server required

**Limitations**:
- Credentials in URLs (visible in logs)
- Basic authentication (not OAuth/SAML)
- No user management interface

**Best Practices**:
- Use HTTPS/RTSP over TLS in production
- Rotate credentials periodically
- Use strong, unique passwords per stream
- Consider VPN for additional security

---

## Hardware Acceleration

### Purpose

Offload video encoding from CPU to GPU for better performance and efficiency.

### Benefits

**Performance**:
- 10x faster encoding
- 80-90% less CPU usage
- Enables more concurrent streams

**Quality**:
- Better quality at same bitrate (newer encoders)
- Real-time encoding of high-resolution streams

### Options

#### None (Software Encoding)

**Encoder**: libx264
**CPU Usage**: ~100% per 1080p stream
**Pros**: Works everywhere, no special hardware
**Cons**: High CPU usage, limited concurrent streams

**When to Use**:
- Testing and development
- No GPU available
- Low-resolution streams (<720p)

#### NVIDIA NVENC

**Encoder**: h264_nvenc / hevc_nvenc
**Requirements**: NVIDIA GPU (GTX 10-series or newer)
**CPU Usage**: ~5-10% per 1080p stream
**Quality**: Excellent (comparable to x264 medium preset)

**Supported GPUs**:
- GTX 1050 and newer
- RTX 20/30/40 series
- Quadro/Tesla professional cards

**Setup Requirements**:
- nvidia-docker2 installed
- NVIDIA drivers on host
- GPU passed through to container

**Concurrent Streams**:
- Consumer GPUs: 2-3 streams (driver limit)
- Professional GPUs: Unlimited

**Performance**:
- 1080p encoding: ~60 FPS
- 4K encoding: ~30 FPS

#### Intel QuickSync (QSV)

**Encoder**: h264_qsv / hevc_qsv
**Requirements**: Intel CPU (6th gen or newer)
**CPU Usage**: ~10-15% per 1080p stream
**Quality**: Good (improved in newer generations)

**Supported CPUs**:
- Intel Core 6th gen (Skylake) and newer
- Intel Xeon with integrated graphics

**Setup Requirements**:
- `/dev/dri` device mounted to container
- intel-media-driver or i965 driver

**Concurrent Streams**: 10+ depending on CPU

**Performance**:
- 1080p encoding: ~45 FPS
- 4K encoding: ~20 FPS

#### VA-API (AMD/Intel)

**Encoder**: h264_vaapi / hevc_vaapi
**Requirements**: AMD GPU or Intel GPU
**CPU Usage**: ~15-20% per 1080p stream
**Quality**: Good

**Supported Hardware**:
- AMD Radeon GPUs
- Intel integrated graphics
- Some discrete Intel GPUs

**Setup Requirements**:
- `/dev/dri` device mounted
- mesa-va-drivers installed

**Concurrent Streams**: 5-10 depending on hardware

### Selecting Hardware Acceleration

**Decision Matrix**:
- Have NVIDIA GPU → Use NVENC (best quality/performance)
- Have Intel CPU (6th gen+) → Use QSV (good balance)
- Have AMD GPU → Use VA-API (decent performance)
- None available → Use Software (works everywhere)

**Testing**:
1. Start with software encoding to verify functionality
2. Try hardware encoding options
3. Monitor stream quality and CPU usage
4. Select best option for your hardware

---

## Multi-Protocol Output

### Automatic Protocol Conversion

One source stream automatically available in multiple formats:

### RTSP (Real-Time Streaming Protocol)

**Port**: 8554
**URL**: `rtsp://server:8554/streamname`
**Latency**: <1 second
**Transport**: TCP or UDP

**Players**:
- VLC Media Player
- FFplay
- GStreamer applications
- Most CCTV software

**Use Cases**:
- Security camera viewing
- Low-latency monitoring
- Integration with video management systems

### RTMP (Real-Time Messaging Protocol)

**Port**: 1935
**URL**: `rtmp://server:1935/streamname`
**Latency**: 3-5 seconds

**Players**:
- OBS Studio (for re-streaming)
- FFmpeg
- Some browser players with Flash

**Use Cases**:
- Re-streaming to CDNs
- Integration with legacy systems
- RTMP-based workflows

### HLS (HTTP Live Streaming)

**Port**: 8888
**URL**: `http://server:8888/streamname/index.m3u8`
**Latency**: 1-3 seconds (low-latency mode)

**Players**:
- All modern browsers (via hls.js)
- iOS Safari (native)
- Video.js
- JW Player

**Features**:
- Adaptive bitrate (future feature)
- CDN-friendly
- Firewall-friendly (HTTP)
- Scalable

**Use Cases**:
- Web browser playback
- Mobile devices
- CDN distribution
- Large audiences

### WebRTC (Web Real-Time Communication)

**Port**: 8889
**URL**: `http://server:8889/streamname`
**Latency**: <500ms (sub-second)

**Players**:
- Modern browsers (Chrome, Firefox, Safari)
- WebRTC-enabled applications

**Features**:
- Ultra-low latency
- Peer-to-peer capable
- Encrypted by default
- Interactive applications

**Use Cases**:
- Real-time monitoring
- Interactive video
- Live events
- Video conferencing integration

### SRT (Secure Reliable Transport)

**Port**: 8890
**URL**: `srt://server:8890?streamid=read:streamname`
**Latency**: 1-2 seconds

**Players**:
- FFplay with SRT support
- VLC 3.0+ with SRT
- OBS Studio
- Haivision players

**Features**:
- Error correction
- Encryption
- Handles packet loss
- Firewall traversal

**Use Cases**:
- Internet streaming
- Poor network conditions
- Broadcast contribution
- Professional workflows

---

## Stream Persistence

### Auto-Restart on Server Reboot

**Feature**: Streams automatically restart after container/server restart

### Configuration Storage

**File**: `streams_config.json` (in container `/app`)

**Format**:
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
    "auth_user": "username",
    "auth_pass": "password"
  }
}
```

### Behavior

**On Stream Start**:
1. Stream configuration saved to JSON
2. File persisted to disk immediately

**On Stream Stop**:
1. Configuration removed from JSON
2. File updated immediately

**On Container Start**:
1. Load `streams_config.json`
2. Verify source files exist
3. Reconstruct FFmpeg commands
4. Start all configured streams

**On Container Stop**:
- Configuration preserved
- Streams will restart on next start

### Manual Management

**Disable Auto-Restart**:
Stop stream via UI before shutting down container

**Force Restart**:
```bash
docker-compose restart stream_manager
```

**Clear All Persistent Streams**:
```bash
docker exec stream_manager rm /app/streams_config.json
docker-compose restart stream_manager
```

---

## OBS Studio Integration

### Purpose

Export stream configurations as OBS Studio scene collections for easy setup.

### Usage

1. Create multiple streams in web UI
2. Click "Export OBS Scene" button
3. Download generated JSON file
4. Open OBS Studio
5. Go to: Scene Collection → Import
6. Select downloaded file
7. Switch to imported scene collection

### Generated Scene Structure

**Scene per Stream**:
- Scene name matches stream name
- Single media source per scene
- Configured with optimal settings

**Source Configuration**:
- Source Type: Media Source
- URL: RTSP/RTMP/HLS URL for stream
- Hardware decoding enabled (if available)
- Buffering optimized for live streaming

### Example Scene Collection

```json
{
  "name": "MediaMTX Streams",
  "scenes": [
    {
      "name": "stream1",
      "sources": [
        {
          "name": "stream1_source",
          "type": "ffmpeg_source",
          "settings": {
            "input": "rtsp://server:8554/stream1",
            "is_local_file": false,
            "hw_decode": true
          }
        }
      ]
    }
  ]
}
```

### Use Cases

**Multi-Camera Production**:
- Create scenes for each camera stream
- Switch between cameras in OBS
- Add overlays and transitions

**Re-Streaming**:
- Ingest streams from MediaMTX
- Composite multiple streams
- Stream to YouTube/Twitch

**Recording**:
- Record individual streams from OBS
- Add commentary or overlays
- Post-production editing

---

## Bulk Operations

### Select Multiple Streams

**Feature**: Checkboxes on each stream card

**Usage**:
1. Click checkbox on streams to select
2. "Stop Selected" button appears
3. Click to stop all selected streams

### Stop All Streams

**Feature**: Single button to stop everything

**Usage**:
1. Click "Stop All Streams" button
2. Confirm action
3. All streams terminated

**Behavior**:
- All FFmpeg processes terminated gracefully
- All streams removed from active list
- Stream configurations preserved (will auto-restart)

### Refresh Streams

**Feature**: Manual refresh of stream list

**Usage**:
- Click "Refresh" button
- Stream list and metrics updated immediately

**Auto-Refresh**: List updates every 2 seconds automatically

---

## File Management

### Server File Browser

**Access**: Click "Browse Server" button in stream configuration

**Features**:
- Navigate filesystem directories
- Breadcrumb navigation
- File size display
- File type filtering
- Video file highlighting

**Navigation**:
- Click folder to enter
- Click breadcrumb item to go back
- Double-click file to select

**Supported Locations**:
- `/media` directory (primary)
- Mounted volumes
- Network shares (if mounted)

### File Upload

**Access**: Select "Upload File" option in stream configuration

**Process**:
1. Click file input
2. Select local video file
3. Upload progress displayed
4. File saved to `/media`
5. Available immediately for streaming

**Upload Features**:
- Progress bar with percentage
- Cancel capability
- Retry on failure
- File validation

### Storage Locations

**Media Files**: `/media`
- User video files
- Uploaded files
- Organized as desired

**Recordings**: `/recordings/{stream_name}/`
- Organized by stream
- Timestamped filenames
- Automatic organization

---

## Real-Time Monitoring

### Stream Metrics

Each stream card displays:

**Status Badge**:
- 🟢 Running - Stream active and healthy
- 🔴 Error - Stream failed or stopped unexpectedly
- 🟡 Starting - Stream initialization in progress

**Viewer Count**:
- Number of active connections to stream
- Real-time updates
- Across all protocols

**Bitrate**:
- Current output bitrate
- In Mbps (megabits per second)
- Actual vs. configured

**Uptime**:
- Time since stream started
- Format: HH:MM:SS
- Resets on stream restart

**Recording Indicator**:
- 🔴 REC - Recording active
- Displayed when recording enabled

**Authentication Indicator**:
- 🔒 - Stream is password-protected

### Auto-Update

**Polling Interval**: 2 seconds

**Updated Information**:
- Stream status
- Viewer count
- Bitrate
- New streams
- Removed streams

### Manual Refresh

Click "Refresh" button for immediate update

---

## User Interface

### Design Philosophy

**Goals**:
- Intuitive operation
- Minimal clicks to common tasks
- Clear visual feedback
- Responsive layout

### Main Dashboard

**Layout**:
- Header with title and controls
- Button bar for actions
- Grid of stream cards
- Modals for configuration

**Color Coding**:
- Blue - Primary actions
- Red - Destructive actions (stop, delete)
- Green - Success states
- Gray - Secondary actions

### Dark Mode

**Toggle**: Moon icon in header

**Features**:
- Persistent preference (localStorage)
- Smooth transitions
- Optimized colors for readability
- Reduced eye strain

**Colors**:
- Light mode: White backgrounds, dark text
- Dark mode: Dark backgrounds, light text

### Responsive Design

**Breakpoints**:
- Desktop: 1200px+ (3-column grid)
- Tablet: 768-1199px (2-column grid)
- Mobile: <768px (single column)

**Mobile Optimizations**:
- Touch-friendly buttons
- Simplified layouts
- Collapsible sections
- Optimized modal sizes

### Accessibility

**Features**:
- Semantic HTML
- ARIA labels
- Keyboard navigation
- Focus indicators
- Color contrast compliance (WCAG AA)

### Stream Cards

**Information Display**:
- Stream name (large, prominent)
- Source file/camera URL
- Protocol badge
- Metrics (viewers, bitrate, uptime)
- Status indicator
- Action buttons

**Actions**:
- Stop Stream
- View URLs (collapsible)
- Select for bulk operations

### Configuration Modal

**Sections**:
1. Stream name input
2. Source selection (radio buttons)
3. Source-specific fields
4. Encoding configuration
5. Recording toggle
6. Authentication toggle
7. Action buttons

**Validation**:
- Required fields highlighted
- Real-time error messages
- Submit disabled until valid

**User Experience**:
- Auto-focus on first field
- Enter key submits form
- Escape key cancels
- Remembers last selection

### Recordings Modal

**Layout**:
- List of recordings
- Grouped by stream
- File information
- Action buttons

**Actions Per Recording**:
- Download (preserves filename)
- Delete (with confirmation)

**Information Displayed**:
- Stream name
- Filename
- File size
- Recording date/time
- Total storage used

### Notifications

**Toast Notifications**:
- Success messages (green)
- Error messages (red)
- Info messages (blue)
- Auto-dismiss after 5 seconds

**Messages**:
- Stream started successfully
- Stream stopped
- Upload complete
- Error details
- Validation failures

---

## Advanced Features

### Custom FFmpeg Parameters

**Future Feature**: Allow advanced users to specify custom FFmpeg flags

**Potential Options**:
- Custom video filters
- Audio processing
- Multiple audio tracks
- Subtitles
- Custom muxing options

### Multi-Bitrate Streaming

**Future Feature**: ABR (Adaptive Bitrate) support

**Implementation**:
- Multiple FFmpeg processes
- Different resolution/bitrate combinations
- HLS manifest with variants
- Automatic quality switching

### Stream Scheduling

**Future Feature**: Start/stop streams on schedule

**Options**:
- Cron-like scheduling
- One-time scheduled starts
- Recurring schedules
- Time-zone aware

### Webhooks

**Future Feature**: HTTP callbacks on events

**Events**:
- Stream started
- Stream stopped
- Stream error
- Recording started
- Recording stopped
- Viewer count thresholds

### Analytics

**Future Feature**: Historical metrics and reporting

**Metrics**:
- Viewer count over time
- Bandwidth usage
- Stream uptime
- Error rates
- Popular streams

---

## Troubleshooting Features

### Stream Health Detection

**Automatic Monitoring**:
- Process status checked every API call
- FFmpeg stderr monitored for errors
- MediaMTX connectivity tested

**Error States**:
- Process crashed
- MediaMTX unavailable
- Source file missing
- Encoding errors

### Debug Information

**Available in Logs**:
- Full FFmpeg command
- FFmpeg output (stdout/stderr)
- MediaMTX responses
- API request/response logs

**Access Logs**:
```bash
docker-compose logs -f stream_manager
docker-compose logs -f mediamtx
```

### Recovery Actions

**Automatic**:
- Graceful process termination
- Clean up on errors
- Persist configuration

**Manual**:
- Restart individual streams
- Restart all streams
- Clear configuration
- Rebuild containers
