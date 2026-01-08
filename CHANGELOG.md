# Changelog

All notable changes to the MediaMTX Stream Manager will be documented in this file.

## [1.1.0] - 2026-01-08

### Added
- **Audio Codec Selection**: Choose between Opus (WebRTC-compatible) or AAC (RTSP/RTMP-compatible) audio codecs
- **Advanced Options UI**: Collapsible section for Publishing Protocol, Audio Codec, and Hardware Acceleration settings
- **Dark Mode Toggle**: Switch between light and dark themes
- **Traefik Integration**: Full support for Traefik reverse proxy with HTTPS
- **WebRTC Support**: Properly configured WebRTC with ICE server support
- **Stream Persistence**: Automatically restart streams after container/server reboot
- **File Browser**: Browse server filesystem to select video sources
- **Recording Management**: View, download, and delete stream recordings through web UI
- **Bulk Operations**: Select multiple streams for simultaneous stop operations

### Changed
- **UI Layout**: Centered control buttons for cleaner appearance
- **Recording Format**: Changed from MP4 to fMP4 (fragmented MP4) for better MediaMTX compatibility
- **Environment Variables**: Switched from `SERVER_HOST` to `SERVER_IP` for clarity
- **Default Audio Codec**: Opus is now default for WebRTC compatibility
- **MediaMTX Version**: Updated to v1.15.6

### Fixed
- **Template Caching**: HTML templates now properly reload with version parameter updates
- **Docker Networking**: Added missing `/streams` volume mount
- **WebRTC Peer Connections**: Fixed by adding `webrtcAdditionalHosts` configuration
- **Stream URL Generation**: Now uses correct server IP instead of Docker internal IP
- **RTSP Transport**: Supports both TCP and UDP transport negotiation

### Technical Details
- Flask backend now accepts `audio_codec` parameter in stream creation API
- FFmpeg commands dynamically adjust based on selected audio codec
- CSS/JS versioning system prevents browser caching issues
- MediaMTX configuration supports fMP4 recording format

## [1.0.0] - Initial Release

### Features
- Web-based stream management interface
- Multi-protocol support (RTSP, RTMP, SRT, HLS, WebRTC)
- Hardware acceleration support (NVIDIA NVENC, Intel QuickSync, VA-API)
- Multiple video sources (files, IP cameras, uploads)
- Docker Compose deployment
- Stream authentication
- Real-time stream monitoring
