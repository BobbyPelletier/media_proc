# Distribution Package Notes

This document describes what was sanitized and prepared for distribution.

## Sanitization Summary

The following personal/environment-specific information has been removed or templated:

### docker-compose.yml
- **Changed**: `SERVER_IP=192.168.0.8` → `SERVER_IP=YOUR_SERVER_IP`
- **Commented Out**: All Traefik labels (user must configure with their domain)
- **Commented Out**: `proxy` network (optional for Traefik users)
- Instructions added for enabling Traefik support

### mediamtx.yml
- **Changed**: `webrtcAdditionalHosts: [192.168.0.8]` → `webrtcAdditionalHosts: [YOUR_SERVER_IP]`
- Clear instructions added in comments

## Required User Configuration

Before deployment, users MUST configure:

1. **SERVER_IP** in `docker-compose.yml` (line 47)
2. **webrtcAdditionalHosts** in `mediamtx.yml` (line 75)

Optional configuration:
3. Traefik labels in `docker-compose.yml` (if using reverse proxy)
4. Hardware acceleration settings (if using GPU)

## Distribution Contents

### Configuration Files
- `docker-compose.yml` - Sanitized, ready for customization
- `mediamtx.yml` - Sanitized, WebRTC placeholder needs configuration
- `.env.example` - Template for environment variables
- `.gitignore` - Configured for the project

### Documentation
- `DISTRIBUTION_README.md` - **START HERE** - Quick deployment guide
- `README.md` - Complete user manual
- `FEATURES.md` - Detailed feature documentation
- `TROUBLESHOOTING.md` - Common issues and solutions
- `CHANGELOG.md` - Version history and recent changes
- `ARCHITECTURE.md` - Technical architecture details
- `QUICK_START.md` - Fast setup guide
- `DEPLOYMENT_SUMMARY.md` - Deployment information
- `MANIFEST.md` - File listing and descriptions
- `DISTRIBUTION_NOTES.md` - This file

### Application Code
- `web/` - Complete Flask application
  - `app.py` - Backend API (23KB)
  - `Dockerfile` - Container build instructions
  - `requirements.txt` - Python dependencies
  - `templates/index.html` - Web UI (8.6KB)
  - `static/css/style.css` - Styles with dark mode (22KB)
  - `static/js/app.js` - Frontend logic (30KB)

### Scripts
- `setup.sh` - Automated deployment script

## Features Included

✅ Multi-protocol streaming (RTSP, RTMP, SRT, HLS, WebRTC)
✅ Audio codec selection (Opus/AAC)
✅ Hardware acceleration support
✅ Stream authentication
✅ Recording management
✅ Dark mode UI
✅ File browser
✅ Bulk operations
✅ Stream persistence
✅ Traefik integration (requires configuration)

## Version Information

- **Distribution Date**: January 8, 2026
- **Version**: 1.1.0
- **MediaMTX**: v1.15.6 (via Docker latest tag)
- **Python**: 3.11
- **Flask**: 3.0.0

## Security Considerations

This distribution:
- ❌ Does NOT contain any credentials or passwords
- ❌ Does NOT expose services by default (local only)
- ✅ Includes instructions for secure deployment
- ✅ Provides example for Traefik SSL integration
- ✅ Documents firewall requirements

Users should:
1. Configure firewall rules appropriately
2. Use SSL/TLS for production (via Traefik or similar)
3. Enable stream authentication for sensitive content
4. Keep Docker images updated
5. Not expose MediaMTX API port to internet

## Testing Recommendations

After deployment, test:
1. Web UI access at `http://SERVER_IP:5000`
2. Create a test stream with a video file
3. Verify RTSP stream: `vlc rtsp://SERVER_IP:8554/test`
4. Verify HLS stream: `vlc http://SERVER_IP:8888/test`
5. Verify WebRTC (after configuring webrtcAdditionalHosts)
6. Test recording functionality
7. Test authentication if enabled

## Support Resources

- MediaMTX Documentation: https://github.com/bluenviron/mediamtx
- FFmpeg Documentation: https://ffmpeg.org/documentation.html
- Flask Documentation: https://flask.palletsprojects.com/
- Docker Compose Documentation: https://docs.docker.com/compose/

## Known Limitations

1. **RTSP with Android ExoPlayer**: Some Android players may have issues with RTSP due to transport negotiation. Use HLS or SRT instead.
2. **WebRTC Requires Configuration**: Must set `webrtcAdditionalHosts` correctly
3. **Hardware Acceleration**: Requires compatible hardware and proper Docker device access
4. **Recording Format**: Only fMP4 format supported by MediaMTX v1.x

## Changelog Highlights

### v1.1.0 (Current)
- Added audio codec selection
- Added advanced options UI
- Added dark mode
- Fixed WebRTC configuration
- Improved Traefik integration
- Updated documentation

See `CHANGELOG.md` for complete version history.
