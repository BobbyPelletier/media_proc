#!/usr/bin/env python3
"""
MediaMTX Stream Manager - Flask Backend
Manages video streams with MediaMTX and FFmpeg
"""

import os
import subprocess
import json
import uuid
import socket
import requests
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import threading
import signal

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/streams'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 * 1024  # 5GB max file size
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'mkv', 'avi', 'mov', 'flv', 'ts', 'webm'}
app.config['STREAMS_CONFIG_FILE'] = '/streams/streams_config.json'
app.config['RECORDINGS_FOLDER'] = '/recordings'

# Store active stream processes
active_streams = {}
stream_lock = threading.Lock()

def get_server_ip():
    """Get the server's IP address"""
    # Try to get from environment variable first
    server_ip = os.getenv('SERVER_IP')
    if server_ip:
        return server_ip

    # Try to determine from Docker host
    try:
        # Get the default route gateway (Docker host)
        with open('/proc/net/route') as f:
            for line in f:
                fields = line.strip().split()
                if fields[1] == '00000000':  # Default route
                    gateway = socket.inet_ntoa(bytes.fromhex(fields[2])[::-1])
                    return gateway
    except:
        pass

    # Fallback to hostname resolution
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except:
        return 'localhost'

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_media_files():
    """Get list of media files in the streams directory"""
    streams_path = Path(app.config['UPLOAD_FOLDER'])
    if not streams_path.exists():
        return []

    media_files = []
    for ext in app.config['ALLOWED_EXTENSIONS']:
        media_files.extend(streams_path.glob(f'*.{ext}'))

    return [f.name for f in sorted(media_files)]

def get_mediamtx_api_url():
    """Get MediaMTX API base URL"""
    mediamtx_host = os.getenv('MEDIAMTX_HOST', 'mediamtx')
    return f'http://{mediamtx_host}:9997'

def get_mediamtx_paths():
    """Get all paths/streams from MediaMTX API"""
    try:
        response = requests.get(f'{get_mediamtx_api_url()}/v3/paths/list', timeout=2)
        if response.status_code == 200:
            data = response.json()
            return data.get('items', [])
        return []
    except Exception as e:
        print(f"Error fetching MediaMTX paths: {e}")
        return []

def get_mediamtx_path_info(path_name):
    """Get detailed information about a specific path"""
    try:
        response = requests.get(f'{get_mediamtx_api_url()}/v3/paths/get/{path_name}', timeout=2)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching path info for {path_name}: {e}")
        return None

def format_bytes(bytes_value):
    """Format bytes to human-readable string"""
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024 * 1024:
        return f"{bytes_value / 1024:.1f} KB"
    elif bytes_value < 1024 * 1024 * 1024:
        return f"{bytes_value / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_value / (1024 * 1024 * 1024):.2f} GB"

def calculate_bitrate(bytes_received, bytes_sent):
    """Calculate approximate bitrate from byte counts"""
    # This is a rough estimate - would need time delta for accuracy
    total_bytes = bytes_received + bytes_sent
    return format_bytes(total_bytes)

def save_streams_config():
    """Save current stream configurations to JSON file for persistence"""
    try:
        config_file = app.config['STREAMS_CONFIG_FILE']
        streams_to_save = []

        with stream_lock:
            for stream_id, stream_data in active_streams.items():
                # Only save running streams
                if stream_data['status'] == 'running':
                    config = {
                        'id': stream_id,
                        'name': stream_data['name'],
                        'protocol': stream_data['protocol'],
                        'bitrate': stream_data.get('bitrate', '2M'),
                        'resolution': stream_data.get('resolution', 'Original'),
                        'source_type': stream_data.get('source_type', 'file'),
                        'file': stream_data['file']
                    }
                    streams_to_save.append(config)

        # Ensure directory exists
        os.makedirs(os.path.dirname(config_file), exist_ok=True)

        with open(config_file, 'w') as f:
            json.dump(streams_to_save, f, indent=2)

        print(f"Saved {len(streams_to_save)} stream configurations")
    except Exception as e:
        print(f"Error saving stream configurations: {e}")

def load_streams_config():
    """Load and auto-start streams from configuration file"""
    try:
        config_file = app.config['STREAMS_CONFIG_FILE']

        if not os.path.exists(config_file):
            print("No saved stream configuration found")
            return

        with open(config_file, 'r') as f:
            saved_streams = json.load(f)

        print(f"Loading {len(saved_streams)} saved streams")

        for stream_config in saved_streams:
            try:
                stream_id = stream_config.get('id', str(uuid.uuid4()))
                stream_name = stream_config['name']
                protocol = stream_config['protocol']
                bitrate = stream_config.get('bitrate', '2M')
                resolution = stream_config.get('resolution')
                if resolution == 'Original':
                    resolution = None
                source_type = stream_config.get('source_type', 'file')
                file_info = stream_config['file']

                # Determine video source
                is_camera = source_type == 'camera'
                if is_camera:
                    # Extract camera URL from file info
                    if file_info.startswith('Camera: '):
                        video_source = file_info.replace('Camera: ', '')
                    else:
                        print(f"Skipping invalid camera config for stream {stream_name}")
                        continue
                else:
                    # File source
                    if os.path.isabs(file_info):
                        video_source = file_info
                    else:
                        video_source = os.path.join(app.config['UPLOAD_FOLDER'], file_info)

                    if not os.path.exists(video_source):
                        print(f"Skipping stream {stream_name} - file not found: {video_source}")
                        continue

                # Build FFmpeg command (no hw_accel from saved config for now, default to opus audio)
                command = build_ffmpeg_command(video_source, stream_name, protocol, bitrate, resolution, is_camera, None, None, None, 'opus')

                # Generate all stream URLs
                server_ip = get_server_ip()
                rtsp_url = f'rtsp://{server_ip}:8554/{stream_name}'
                rtmp_url = f'rtmp://{server_ip}:1935/{stream_name}'
                srt_url = f'srt://{server_ip}:8890?streamid=read:{stream_name}'
                webrtc_url = f'http://{server_ip}:8889/{stream_name}'
                hls_url = f'http://{server_ip}:8888/{stream_name}/index.m3u8'

                # Store stream info
                with stream_lock:
                    active_streams[stream_id] = {
                        'name': stream_name,
                        'protocol': protocol,
                        'status': 'starting',
                        'file': file_info,
                        'source_type': source_type,
                        'bitrate': bitrate,
                        'resolution': resolution or 'Original',
                        'rtsp_url': rtsp_url,
                        'rtmp_url': rtmp_url,
                        'srt_url': srt_url,
                        'webrtc_url': webrtc_url,
                        'hls_url': hls_url,
                        'process': None
                    }

                # Start stream in background thread
                thread = threading.Thread(target=start_stream_process, args=(stream_id, command))
                thread.daemon = True
                thread.start()

                print(f"Auto-started stream: {stream_name}")

            except Exception as e:
                print(f"Error restoring stream {stream_config.get('name', 'unknown')}: {e}")

    except Exception as e:
        print(f"Error loading stream configurations: {e}")

def build_ffmpeg_command(video_source, stream_name, protocol, bitrate='2M', resolution=None, is_camera=False, hw_accel=None, auth_user=None, auth_pass=None, audio_codec='opus'):
    """Build FFmpeg command based on protocol and settings with optional hardware acceleration and authentication

    Args:
        audio_codec: Audio codec to use ('opus' or 'aac'). Default is 'opus' for WebRTC compatibility.
    """
    mediamtx_host = os.getenv('MEDIAMTX_HOST', 'mediamtx')

    # Hardware acceleration input options
    hw_input_opts = []
    if hw_accel == 'vaapi':
        hw_input_opts = ['-hwaccel', 'vaapi', '-hwaccel_device', '/dev/dri/renderD128', '-hwaccel_output_format', 'vaapi']
    elif hw_accel == 'qsv':
        hw_input_opts = ['-hwaccel', 'qsv', '-hwaccel_output_format', 'qsv']
    elif hw_accel == 'nvenc':
        hw_input_opts = ['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda']

    if is_camera:
        # Camera input - no loop, use TCP for RTSP cameras
        base_cmd = ['ffmpeg'] + hw_input_opts + [
            '-rtsp_transport', 'tcp',
            '-i', video_source
        ]
    else:
        # File input - loop indefinitely
        base_cmd = ['ffmpeg'] + hw_input_opts + [
            '-re',
            '-stream_loop', '-1',
            '-i', video_source
        ]

    # Video encoding settings based on hardware acceleration
    if hw_accel == 'nvenc':
        # NVIDIA NVENC encoder
        video_opts = [
            '-c:v', 'h264_nvenc',
            '-preset', 'p4',  # NVENC preset (p1-p7)
            '-tune', 'll',    # Low latency
            '-b:v', bitrate,
            '-maxrate', bitrate,
            '-bufsize', f'{int(bitrate.rstrip("M")) * 2}M',
            '-g', '60',
            '-rc', 'cbr',
            '-rc-lookahead', '20'
        ]
    elif hw_accel == 'qsv':
        # Intel QuickSync encoder
        video_opts = [
            '-c:v', 'h264_qsv',
            '-preset', 'veryfast',
            '-b:v', bitrate,
            '-maxrate', bitrate,
            '-bufsize', f'{int(bitrate.rstrip("M")) * 2}M',
            '-g', '60',
            '-look_ahead', '1'
        ]
    elif hw_accel == 'vaapi':
        # VA-API encoder
        video_opts = [
            '-c:v', 'h264_vaapi',
            '-b:v', bitrate,
            '-maxrate', bitrate,
            '-bufsize', f'{int(bitrate.rstrip("M")) * 2}M',
            '-g', '60'
        ]
    else:
        # Software encoder (libx264)
        video_opts = [
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-tune', 'zerolatency',
            '-b:v', bitrate,
            '-maxrate', bitrate,
            '-bufsize', f'{int(bitrate.rstrip("M")) * 2}M',
            '-g', '60',
            '-keyint_min', '60',
            '-sc_threshold', '0'
        ]

    # Add resolution scaling if specified
    if resolution:
        if hw_accel == 'vaapi':
            video_opts.extend(['-vf', f'scale_vaapi=w={resolution.split(":")[0]}:h={resolution.split(":")[1]}'])
        elif hw_accel == 'qsv':
            video_opts.extend(['-vf', f'scale_qsv=w={resolution.split(":")[0]}:h={resolution.split(":")[1]}'])
        elif hw_accel == 'nvenc':
            video_opts.extend(['-vf', f'scale_cuda={resolution}'])
        else:
            video_opts.extend(['-vf', f'scale={resolution}'])

    # Audio encoding based on selected codec
    # Opus: Required for WebRTC, modern codec with excellent quality
    # AAC: Better compatibility with some RTSP/RTMP clients
    if audio_codec == 'aac':
        audio_opts = [
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '48000'
        ]
    else:  # Default to opus
        audio_opts = [
            '-c:a', 'libopus',
            '-b:a', '128k',
            '-ar', '48000'
        ]

    # Protocol-specific output with optional authentication
    if protocol == 'rtsp':
        if auth_user and auth_pass:
            rtsp_url = f'rtsp://{auth_user}:{auth_pass}@{mediamtx_host}:8554/{stream_name}'
        else:
            rtsp_url = f'rtsp://{mediamtx_host}:8554/{stream_name}'
        output = [
            '-f', 'rtsp',
            '-rtsp_transport', 'tcp',
            rtsp_url
        ]
    elif protocol == 'srt':
        srt_url = f'srt://{mediamtx_host}:8890?streamid=publish:{stream_name}'
        if auth_user and auth_pass:
            # SRT uses passphrase for encryption
            output = ['-f', 'mpegts', '-passphrase', auth_pass, srt_url]
        else:
            output = ['-f', 'mpegts', srt_url]
    elif protocol == 'rtmp':
        if auth_user and auth_pass:
            rtmp_url = f'rtmp://{auth_user}:{auth_pass}@{mediamtx_host}:1935/{stream_name}'
        else:
            rtmp_url = f'rtmp://{mediamtx_host}:1935/{stream_name}'
        output = ['-f', 'flv', rtmp_url]
    else:
        raise ValueError(f'Unsupported protocol: {protocol}')

    return base_cmd + video_opts + audio_opts + output

def start_stream_process(stream_id, command):
    """Start FFmpeg process for streaming"""
    try:
        # Log the command being executed
        print(f"Starting stream {stream_id} with command: {' '.join(command)}")

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )

        with stream_lock:
            active_streams[stream_id]['process'] = process
            active_streams[stream_id]['status'] = 'running'

        # Wait for process to complete or be terminated
        process.wait()

        with stream_lock:
            if stream_id in active_streams:
                if process.returncode != 0:
                    stderr = process.stderr.read().decode('utf-8', errors='ignore')
                    active_streams[stream_id]['status'] = 'failed'
                    active_streams[stream_id]['error'] = stderr[-1000:]  # Last 1000 chars
                    print(f"Stream {stream_id} failed with error: {stderr[-500:]}")
                else:
                    active_streams[stream_id]['status'] = 'stopped'
                    print(f"Stream {stream_id} stopped normally")

    except Exception as e:
        print(f"Exception starting stream {stream_id}: {str(e)}")
        with stream_lock:
            if stream_id in active_streams:
                active_streams[stream_id]['status'] = 'failed'
                active_streams[stream_id]['error'] = str(e)

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/api/media/list', methods=['GET'])
def list_media():
    """List available media files"""
    try:
        files = get_media_files()
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/browse', methods=['POST'])
def browse_files():
    """Browse filesystem for video files"""
    try:
        data = request.json
        current_path = data.get('path', '/')

        # Security: Prevent directory traversal attacks
        # Only allow browsing from root or specific paths
        if not current_path.startswith('/'):
            current_path = '/'

        # Resolve the path
        try:
            resolved_path = Path(current_path).resolve()
        except Exception:
            return jsonify({'success': False, 'error': 'Invalid path'}), 400

        # Check if path exists
        if not resolved_path.exists():
            return jsonify({'success': False, 'error': 'Path does not exist'}), 404

        if not resolved_path.is_dir():
            return jsonify({'success': False, 'error': 'Path is not a directory'}), 400

        items = []

        try:
            # List directories and video files
            for item in sorted(resolved_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                try:
                    item_info = {
                        'name': item.name,
                        'path': str(item),
                        'is_dir': item.is_dir()
                    }

                    if item.is_dir():
                        items.append(item_info)
                    elif item.is_file():
                        # Check if it's a video file
                        ext = item.suffix.lower().lstrip('.')
                        if ext in app.config['ALLOWED_EXTENSIONS']:
                            # Get file size
                            size_bytes = item.stat().st_size
                            if size_bytes < 1024:
                                size_str = f'{size_bytes} B'
                            elif size_bytes < 1024 * 1024:
                                size_str = f'{size_bytes / 1024:.1f} KB'
                            elif size_bytes < 1024 * 1024 * 1024:
                                size_str = f'{size_bytes / (1024 * 1024):.1f} MB'
                            else:
                                size_str = f'{size_bytes / (1024 * 1024 * 1024):.2f} GB'

                            item_info['size'] = size_str
                            items.append(item_info)
                except (PermissionError, OSError):
                    # Skip items we can't access
                    continue
        except PermissionError:
            return jsonify({'success': False, 'error': 'Permission denied'}), 403

        return jsonify({
            'success': True,
            'path': str(resolved_path),
            'items': items
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/media/upload', methods=['POST'])
def upload_media():
    """Upload media file"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Check if file already exists
        if os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'File already exists'}), 400

        file.save(filepath)
        return jsonify({'success': True, 'filename': filename})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/streams/list', methods=['GET'])
def list_streams():
    """List active streams with live MediaMTX metrics"""
    # Get live data from MediaMTX API
    mediamtx_paths = get_mediamtx_paths()
    mediamtx_data = {}

    for path_item in mediamtx_paths:
        path_name = path_item.get('name', '')
        if path_name:
            mediamtx_data[path_name] = path_item

    with stream_lock:
        streams = []
        for stream_id, stream_data in active_streams.items():
            stream_name = stream_data['name']

            # Get live metrics from MediaMTX if available
            mtx_info = mediamtx_data.get(stream_name, {})

            # Extract useful metrics
            source_ready = mtx_info.get('ready', False)
            num_readers = len(mtx_info.get('readers', []))
            bytes_received = mtx_info.get('bytesReceived', 0)
            bytes_sent = mtx_info.get('bytesSent', 0)

            # Calculate health status
            health_status = 'healthy' if source_ready and num_readers >= 0 else 'waiting'
            if stream_data['status'] == 'failed':
                health_status = 'error'

            stream_info = {
                'id': stream_id,
                'name': stream_name,
                'protocol': stream_data['protocol'],
                'status': stream_data['status'],
                'file': stream_data['file'],
                'bitrate': stream_data.get('bitrate', 'N/A'),
                'resolution': stream_data.get('resolution', 'N/A'),
                'rtsp_url': stream_data.get('rtsp_url', ''),
                'rtmp_url': stream_data.get('rtmp_url', ''),
                'srt_url': stream_data.get('srt_url', ''),
                'webrtc_url': stream_data.get('webrtc_url', ''),
                'hls_url': stream_data.get('hls_url', ''),
                'error': stream_data.get('error'),
                # Live metrics from MediaMTX
                'live_metrics': {
                    'source_ready': source_ready,
                    'viewers': num_readers,
                    'bytes_received': format_bytes(bytes_received),
                    'bytes_sent': format_bytes(bytes_sent),
                    'health_status': health_status
                }
            }
            streams.append(stream_info)

        return jsonify({'success': True, 'streams': streams})

@app.route('/api/streams/start', methods=['POST'])
def start_stream():
    """Start a new stream"""
    try:
        data = request.json
        video_file = data.get('file')
        camera_url = data.get('camera_url')
        stream_name = data.get('name')
        protocol = data.get('protocol', 'rtsp')
        bitrate = data.get('bitrate', '2M')
        resolution = data.get('resolution')
        hw_accel = data.get('hw_accel')  # Hardware acceleration: nvenc, qsv, vaapi, or None
        enable_recording = data.get('enable_recording', False)  # Enable recording
        auth_user = data.get('auth_user')  # Optional authentication username
        auth_pass = data.get('auth_pass')  # Optional authentication password
        audio_codec = data.get('audio_codec', 'opus')  # Audio codec: opus (default) or aac

        if not stream_name:
            return jsonify({'success': False, 'error': 'Stream name is required'}), 400

        # Configure recording in MediaMTX if enabled
        if enable_recording:
            try:
                mediamtx_api = f'http://mediamtx:9997/v3/config/paths/patch/{stream_name}'
                recording_config = {
                    'record': True,
                    'recordPath': f'/recordings/{stream_name}/%Y-%m-%d_%H-%M-%S-%f'
                }
                requests.patch(mediamtx_api, json=recording_config, timeout=5)
            except Exception as e:
                print(f"Warning: Could not configure recording in MediaMTX: {e}")

        # Determine source type
        is_camera = False
        if camera_url:
            # IP Camera source
            video_source = camera_url
            is_camera = True
            source_type = 'camera'
        elif video_file:
            # File source - handle both relative filenames and absolute paths
            if os.path.isabs(video_file):
                # Absolute path from file browser
                video_source = video_file
            else:
                # Relative filename from dropdown
                video_source = os.path.join(app.config['UPLOAD_FOLDER'], video_file)

            if not os.path.exists(video_source):
                return jsonify({'success': False, 'error': 'Video file not found'}), 404
            source_type = 'file'
        else:
            return jsonify({'success': False, 'error': 'Either file or camera_url is required'}), 400

        # Generate unique stream ID
        stream_id = str(uuid.uuid4())

        # Build FFmpeg command
        command = build_ffmpeg_command(video_source, stream_name, protocol, bitrate, resolution, is_camera, hw_accel, auth_user, auth_pass, audio_codec)

        # Generate all stream URLs (MediaMTX provides all protocols from single input)
        server_ip = get_server_ip()

        # Add authentication to URLs if provided
        if auth_user and auth_pass:
            auth_prefix = f'{auth_user}:{auth_pass}@'
            rtsp_url = f'rtsp://{auth_prefix}{server_ip}:8554/{stream_name}'
            rtmp_url = f'rtmp://{auth_prefix}{server_ip}:1935/{stream_name}'
        else:
            rtsp_url = f'rtsp://{server_ip}:8554/{stream_name}'
            rtmp_url = f'rtmp://{server_ip}:1935/{stream_name}'

        srt_url = f'srt://{server_ip}:8890?streamid=read:{stream_name}'
        webrtc_url = f'http://{server_ip}:8889/{stream_name}'
        hls_url = f'http://{server_ip}:8888/{stream_name}/index.m3u8'

        # Store stream info
        with stream_lock:
            active_streams[stream_id] = {
                'name': stream_name,
                'protocol': protocol,
                'status': 'starting',
                'file': video_file if not is_camera else f'Camera: {camera_url}',
                'source_type': source_type,
                'bitrate': bitrate,
                'resolution': resolution or 'Original',
                'rtsp_url': rtsp_url,
                'rtmp_url': rtmp_url,
                'srt_url': srt_url,
                'webrtc_url': webrtc_url,
                'hls_url': hls_url,
                'process': None
            }

        # Start stream in background thread
        thread = threading.Thread(target=start_stream_process, args=(stream_id, command))
        thread.daemon = True
        thread.start()

        # Save stream configuration for persistence
        save_streams_config()

        return jsonify({
            'success': True,
            'stream_id': stream_id,
            'rtsp_url': rtsp_url,
            'rtmp_url': rtmp_url,
            'srt_url': srt_url,
            'webrtc_url': webrtc_url,
            'hls_url': hls_url
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/streams/stop/<stream_id>', methods=['POST'])
def stop_stream(stream_id):
    """Stop a running stream"""
    try:
        with stream_lock:
            if stream_id not in active_streams:
                return jsonify({'success': False, 'error': 'Stream not found'}), 404

            stream_data = active_streams[stream_id]
            process = stream_data.get('process')

            if process and process.poll() is None:
                # Terminate process gracefully
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()

                stream_data['status'] = 'stopped'

            # Remove from active streams
            del active_streams[stream_id]

        # Update saved configuration
        save_streams_config()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/streams/stop-all', methods=['POST'])
def stop_all_streams():
    """Stop all running streams"""
    try:
        stopped_count = 0
        with stream_lock:
            for stream_id, stream_data in list(active_streams.items()):
                process = stream_data.get('process')
                if process and process.poll() is None:
                    if os.name != 'nt':
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    else:
                        process.terminate()
                    stopped_count += 1

            active_streams.clear()

        # Update saved configuration
        save_streams_config()

        return jsonify({'success': True, 'stopped': stopped_count})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recordings/list', methods=['GET'])
def list_recordings():
    """List all recordings organized by stream path"""
    try:
        recordings_path = Path(app.config['RECORDINGS_FOLDER'])
        if not recordings_path.exists():
            return jsonify({'success': True, 'recordings': []})

        recordings = []

        # Walk through recordings directory
        for stream_dir in sorted(recordings_path.iterdir()):
            if stream_dir.is_dir():
                stream_name = stream_dir.name
                stream_recordings = []

                for recording_file in sorted(stream_dir.iterdir(), reverse=True):
                    if recording_file.is_file():
                        # Get file info
                        stat = recording_file.stat()
                        size_bytes = stat.st_size
                        modified_time = stat.st_mtime

                        stream_recordings.append({
                            'filename': recording_file.name,
                            'path': str(recording_file.relative_to(recordings_path)),
                            'size': format_bytes(size_bytes),
                            'size_bytes': size_bytes,
                            'modified': modified_time
                        })

                if stream_recordings:
                    recordings.append({
                        'stream': stream_name,
                        'count': len(stream_recordings),
                        'files': stream_recordings
                    })

        return jsonify({'success': True, 'recordings': recordings})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recordings/download/<path:file_path>', methods=['GET'])
def download_recording(file_path):
    """Download a recording file"""
    try:
        from flask import send_file

        recordings_path = Path(app.config['RECORDINGS_FOLDER'])
        file_full_path = recordings_path / file_path

        # Security check: ensure file is within recordings directory
        if not str(file_full_path.resolve()).startswith(str(recordings_path.resolve())):
            return jsonify({'success': False, 'error': 'Invalid file path'}), 403

        if not file_full_path.exists():
            return jsonify({'success': False, 'error': 'File not found'}), 404

        return send_file(
            str(file_full_path),
            as_attachment=True,
            download_name=file_full_path.name
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recordings/delete/<path:file_path>', methods=['DELETE'])
def delete_recording(file_path):
    """Delete a recording file"""
    try:
        recordings_path = Path(app.config['RECORDINGS_FOLDER'])
        file_full_path = recordings_path / file_path

        # Security check: ensure file is within recordings directory
        if not str(file_full_path.resolve()).startswith(str(recordings_path.resolve())):
            return jsonify({'success': False, 'error': 'Invalid file path'}), 403

        if not file_full_path.exists():
            return jsonify({'success': False, 'error': 'File not found'}), 404

        # Delete the file
        file_full_path.unlink()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/streams/bulk-stop', methods=['POST'])
def bulk_stop_streams():
    """Stop multiple streams at once"""
    try:
        data = request.json
        stream_ids = data.get('stream_ids', [])

        if not stream_ids:
            return jsonify({'success': False, 'error': 'No stream IDs provided'}), 400

        stopped_count = 0
        errors = []

        for stream_id in stream_ids:
            try:
                with stream_lock:
                    if stream_id in active_streams:
                        stream_data = active_streams[stream_id]
                        process = stream_data.get('process')

                        if process and process.poll() is None:
                            if os.name != 'nt':
                                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                            else:
                                process.terminate()
                            stopped_count += 1

                        del active_streams[stream_id]
            except Exception as e:
                errors.append(f"Error stopping {stream_id}: {str(e)}")

        # Update saved configuration
        save_streams_config()

        return jsonify({
            'success': True,
            'stopped': stopped_count,
            'errors': errors
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/obs/export/<stream_id>', methods=['GET'])
def export_obs_config(stream_id):
    """Generate OBS Studio scene configuration for a stream"""
    try:
        with stream_lock:
            if stream_id not in active_streams:
                return jsonify({'success': False, 'error': 'Stream not found'}), 404

            stream_data = active_streams[stream_id]

        stream_name = stream_data['name']
        rtsp_url = stream_data['rtsp_url']

        # OBS Studio scene collection format
        obs_config = {
            "current_scene": stream_name,
            "current_program_scene": stream_name,
            "scene_order": [
                {"name": stream_name}
            ],
            "name": f"MediaMTX - {stream_name}",
            "sources": [
                {
                    "versioned_id": "ffmpeg_source",
                    "name": f"{stream_name}_source",
                    "id": "ffmpeg_source",
                    "settings": {
                        "input": rtsp_url,
                        "input_format": "",
                        "is_local_file": False,
                        "looping": True,
                        "restart_on_activate": True,
                        "clear_on_media_end": False,
                        "reconnect_delay_sec": 10,
                        "hw_decode": True
                    },
                    "volume": 1.0,
                    "muted": False
                }
            ],
            "scenes": [
                {
                    "name": stream_name,
                    "sources": [
                        {
                            "name": f"{stream_name}_source",
                            "id": 1,
                            "enabled": True,
                            "prev_ver_enabled": True,
                            "visible": True,
                            "locked": False,
                            "pos": {"x": 0.0, "y": 0.0},
                            "scale": {"x": 1.0, "y": 1.0},
                            "rot": 0.0,
                            "crop": {
                                "left": 0,
                                "top": 0,
                                "right": 0,
                                "bottom": 0
                            },
                            "bounds": {
                                "type": "OBS_BOUNDS_NONE",
                                "alignment": 0,
                                "x": 0.0,
                                "y": 0.0
                            }
                        }
                    ]
                }
            ]
        }

        # Return as JSON file download
        from flask import Response
        import json as json_module

        response = Response(
            json_module.dumps(obs_config, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename=obs_scene_{stream_name}.json'}
        )

        return response

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Load and auto-start saved streams
    print("Loading saved stream configurations...")
    load_streams_config()

    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
