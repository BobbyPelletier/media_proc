# MediaMTX Stream Manager - File Manifest

This document lists all files included in the deployment package and their purposes.

## Project Structure

```
media_proc_final/
├── README.md                       # Main documentation and quick start guide
├── ARCHITECTURE.md                 # System design and technical architecture
├── FEATURES.md                     # Detailed feature documentation
├── TROUBLESHOOTING.md              # Common issues and solutions
├── MANIFEST.md                     # This file - complete file listing
├── docker-compose.yml              # Container orchestration configuration
├── mediamtx.yml                    # MediaMTX server configuration
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
├── setup.sh                        # Automated setup script
└── web/                            # Flask web application
    ├── Dockerfile                  # Container build instructions
    ├── requirements.txt            # Python dependencies
    ├── app.py                      # Flask backend application
    ├── templates/
    │   └── index.html              # Web UI HTML template
    └── static/
        ├── css/
        │   └── style.css           # UI stylesheet
        └── js/
            └── app.js              # Frontend JavaScript application
```

## File Descriptions

### Documentation Files

#### README.md
- **Purpose**: Primary documentation file
- **Contains**:
  - Feature overview
  - Quick start guide
  - Installation instructions
  - Configuration guide
  - Usage examples
  - API documentation
- **Audience**: All users

#### ARCHITECTURE.md
- **Purpose**: Technical system design documentation
- **Contains**:
  - Component architecture diagrams
  - Data flow descriptions
  - Service interactions
  - Storage architecture
  - Network architecture
  - Security design
  - Technology choices and rationale
- **Audience**: Developers, system administrators

#### FEATURES.md
- **Purpose**: Comprehensive feature documentation
- **Contains**:
  - Detailed description of all features
  - Usage instructions per feature
  - Configuration options
  - Use cases and examples
  - Technical implementation details
- **Audience**: End users, administrators

#### TROUBLESHOOTING.md
- **Purpose**: Problem diagnosis and resolution guide
- **Contains**:
  - Common issues and solutions
  - Diagnostic commands
  - Error message explanations
  - Performance optimization tips
  - Debug information collection
- **Audience**: All users experiencing issues

#### MANIFEST.md
- **Purpose**: File inventory and descriptions
- **Contains**:
  - Complete file listing
  - Purpose of each file
  - Modification guidelines
- **Audience**: Developers, maintainers

### Configuration Files

#### docker-compose.yml
- **Purpose**: Docker service orchestration
- **Contains**:
  - Service definitions (mediamtx, stream_manager)
  - Port mappings
  - Volume mounts
  - Network configuration
  - Environment variables
- **Modification**: Required for custom deployments
- **Sanitized**: System-specific paths and IPs removed

#### mediamtx.yml
- **Purpose**: MediaMTX server configuration
- **Contains**:
  - Protocol settings (RTSP, RTMP, HLS, WebRTC, SRT)
  - Port configurations
  - Authentication rules
  - Path defaults
  - Recording settings
  - Example stream configurations
- **Modification**: Required for WebRTC (webrtcAdditionalHosts)
- **Sanitized**: Example configurations provided, no specific IPs

#### .env.example
- **Purpose**: Environment variable template
- **Contains**:
  - Server configuration (HOST, PORT)
  - Storage paths (MEDIA_PATH, RECORDINGS_PATH, LOGS_PATH)
  - Hardware acceleration options
  - Protocol ports
- **Usage**: Copy to `.env` and customize
- **Important**: Must be configured before deployment

#### .gitignore
- **Purpose**: Git version control exclusions
- **Contains**:
  - Environment files (.env)
  - Python artifacts
  - Docker volumes
  - Stream configurations with credentials
  - IDE settings
  - OS-specific files
- **Usage**: Prevents committing sensitive or generated files

### Deployment Scripts

#### setup.sh
- **Purpose**: Automated deployment script
- **Contains**:
  - Dependency checks (Docker, Docker Compose)
  - .env file creation from template
  - Directory creation
  - Permission setting
  - Hardware detection
  - Image building and pulling
  - Service startup
  - Success verification
- **Usage**: `chmod +x setup.sh && ./setup.sh`
- **Platform**: Linux/macOS (Windows users use WSL or manual setup)

### Application Files

#### web/Dockerfile
- **Purpose**: Build instructions for stream_manager container
- **Contains**:
  - Base image (Python 3.11-slim)
  - System dependencies (FFmpeg, network tools)
  - Python package installation
  - Application file copying
  - Port exposure (5000)
  - Startup command
- **Modification**: Rarely needed unless adding system dependencies

#### web/requirements.txt
- **Purpose**: Python package dependencies
- **Contains**:
  - Flask 3.0.0 (web framework)
  - requests (HTTP client for MediaMTX API)
  - Other required packages
- **Modification**: Only if adding new Python features

#### web/app.py
- **Purpose**: Flask backend application
- **Contains**:
  - REST API endpoints
  - FFmpeg process management
  - MediaMTX API integration
  - File handling (upload, browse)
  - Recording management
  - Stream persistence logic
  - Authentication handling
- **Lines of Code**: ~800
- **Key Functions**:
  - `start_stream()` - Creates and starts FFmpeg processes
  - `stop_stream()` - Terminates streams
  - `get_streams()` - Returns active stream status
  - `list_files()` - File browser backend
  - `upload_file()` - File upload handler
  - `list_recordings()` - Recording management
- **Modification**: Main file for adding features

#### web/templates/index.html
- **Purpose**: Web UI HTML structure
- **Contains**:
  - Page layout and structure
  - Stream configuration modal
  - File browser modal
  - Recordings modal
  - Form fields and controls
- **Lines**: ~237
- **Modification**: Modify for UI changes
- **Note**: Uses cache-busting query params (v=7)

#### web/static/css/style.css
- **Purpose**: Web UI stylesheet
- **Contains**:
  - Layout and positioning
  - Color schemes (light and dark modes)
  - Responsive design rules
  - Component styling
  - Modal styles
  - Form styling
- **Lines**: ~900
- **Features**:
  - CSS custom properties for theming
  - Media queries for responsive design
  - Dark mode support
- **Modification**: Modify for visual changes

#### web/static/js/app.js
- **Purpose**: Frontend JavaScript application
- **Contains**:
  - API communication
  - DOM manipulation
  - Form handling
  - Modal management
  - Dark mode toggle
  - File upload with progress
  - Real-time stream metrics
  - Bulk operations
- **Lines**: ~1000
- **Key Functions**:
  - `loadStreams()` - Fetches and displays streams
  - `startStream()` - Submits stream configuration
  - `stopStream()` - Stops individual stream
  - `loadFileTree()` - File browser logic
  - `uploadFile()` - File upload with progress
- **Modification**: Modify for frontend feature changes

## Runtime Files (Generated)

These files are created during operation and not included in the repository:

### web/streams_config.json
- **Location**: Container `/app/streams_config.json`
- **Purpose**: Persistent stream configuration
- **Format**: JSON
- **Contains**: All active stream configurations
- **Auto-generated**: Created by app.py
- **Persistence**: Enables stream auto-restart

### Volume Directories

#### media/
- **Purpose**: Video source files
- **Mounted From**: ${MEDIA_PATH} (configured in .env)
- **Contents**: User video files for streaming
- **Permissions**: Read-only recommended

#### recordings/
- **Purpose**: Stream recordings
- **Mounted From**: ${RECORDINGS_PATH}
- **Structure**: Organized by stream name
- **Permissions**: Read-write required
- **Growth**: Grows continuously when recording enabled

#### logs/
- **Purpose**: Application logs
- **Mounted From**: ${LOGS_PATH}
- **Contents**: mediamtx.log
- **Permissions**: Read-write required

#### hls/
- **Purpose**: HLS segment temporary storage
- **Location**: ./hls (local directory)
- **Contents**: .ts and .m3u8 files
- **Cleanup**: Automatic by MediaMTX

## Modification Guidelines

### Safe to Modify

- **README.md**: Update with deployment-specific info
- **.env**: MUST be customized for your environment
- **mediamtx.yml**: Customize ports, authentication, recording
- **docker-compose.yml**: Adjust ports, paths, resource limits
- **web/static/css/style.css**: Visual customization
- **web/templates/index.html**: UI structure changes

### Modify with Caution

- **web/app.py**: Core application logic
- **web/static/js/app.js**: Frontend logic
- **setup.sh**: Deployment automation

### Do Not Modify

- **web/Dockerfile**: Unless adding system dependencies
- **web/requirements.txt**: Unless adding Python packages
- **.gitignore**: Standard exclusions

## Deployment Checklist

Before deploying, ensure you have:

- [ ] Copied .env.example to .env
- [ ] Configured SERVER_HOST in .env
- [ ] Set MEDIA_PATH to your video files location
- [ ] Set RECORDINGS_PATH for recordings storage
- [ ] Reviewed mediamtx.yml (especially webrtcAdditionalHosts)
- [ ] Adjusted docker-compose.yml ports if needed
- [ ] Enabled hardware acceleration (if available)
- [ ] Configured reverse proxy with SSL (if using for production)
- [ ] Opened firewall ports (8554, 1935, 8888, 8889, 8890)
- [ ] Tested Docker and Docker Compose are installed

## Customization Examples

### Change Web UI Port

In `.env`:
```bash
WEB_PORT=8080
```

### Use Different Media Path

In `.env`:
```bash
MEDIA_PATH=/mnt/nas/videos
```

### Add Custom Stream Path

In `mediamtx.yml`:
```yaml
paths:
  my_custom_stream:
    source: publisher
    record: yes
    recordPath: /recordings/custom/%Y-%m-%d_%H-%M-%S-%f
    publishUser: myuser
    publishPass: mypass
```

## Version Information

- **MediaMTX**: Latest (bluenviron/mediamtx:latest)
- **Python**: 3.11-slim
- **Flask**: 3.0.0
- **FFmpeg**: Latest (from Debian repository)
- **Docker Compose**: v3.8 syntax

## File Size Summary

Approximate sizes:
- Documentation: ~100 KB total
- Configuration files: ~10 KB total
- Application code: ~150 KB total
- Docker images (when built): ~500 MB total

## License Information

This deployment package includes:
- Original code: No specific license (customize as needed)
- MediaMTX: MIT License
- FFmpeg: LGPL/GPL (depending on build)
- Flask: BSD License
- Other dependencies: See individual package licenses

## Support

For issues with specific files:
- **Configuration issues**: See TROUBLESHOOTING.md
- **Usage questions**: See README.md and FEATURES.md
- **Architecture questions**: See ARCHITECTURE.md
- **Code modifications**: Review app.py and app.js inline comments
