// MediaMTX Stream Manager - Frontend JavaScript

const API_BASE = '/api';
let streams = {};

// DOM Elements
const modal = document.getElementById('streamModal');
const addStreamBtn = document.getElementById('addStreamBtn');
const stopAllBtn = document.getElementById('stopAllBtn');
const stopSelectedBtn = document.getElementById('stopSelectedBtn');
const refreshBtn = document.getElementById('refreshBtn');
const recordingsBtn = document.getElementById('recordingsBtn');
const closeModal = document.querySelector('.close');
const cancelBtn = document.getElementById('cancelBtn');
const streamForm = document.getElementById('streamForm');
const streamsContainer = document.getElementById('streamsContainer');
const noStreams = document.getElementById('noStreams');

// Recordings Modal Elements
const recordingsModal = document.getElementById('recordingsModal');
const closeRecordingsModal = document.querySelector('.close-recordings');

// Track selected streams for bulk operations
let selectedStreams = new Set();

// File Browser Elements
const fileBrowserModal = document.getElementById('fileBrowserModal');
const browseFilesBtn = document.getElementById('browseFilesBtn');
const closeBrowserModal = document.querySelector('.close-browser');
const cancelBrowserBtn = document.getElementById('cancelBrowserBtn');
const selectFileBtn = document.getElementById('selectFileBtn');
const breadcrumb = document.getElementById('breadcrumb');
const fileList = document.getElementById('fileList');

let currentBrowserPath = '/';
let selectedFilePath = null;

// Source type radio buttons
const sourceTypeRadios = document.querySelectorAll('input[name="sourceType"]');
const existingFileSection = document.getElementById('existingFileSection');
const uploadFileSection = document.getElementById('uploadFileSection');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadMediaFiles();
    loadStreams();
    setupEventListeners();
    initDarkMode();

    // Auto-refresh streams every 5 seconds
    setInterval(loadStreams, 5000);
});

function setupEventListeners() {
    addStreamBtn.addEventListener('click', openModal);
    stopAllBtn.addEventListener('click', stopAllStreams);
    stopSelectedBtn.addEventListener('click', stopSelectedStreams);
    refreshBtn.addEventListener('click', () => {
        loadMediaFiles();
        loadStreams();
    });
    recordingsBtn.addEventListener('click', openRecordingsModal);
    closeModal.addEventListener('click', closeModalDialog);
    cancelBtn.addEventListener('click', closeModalDialog);
    closeRecordingsModal.addEventListener('click', closeRecordingsModalDialog);
    streamForm.addEventListener('submit', handleStreamSubmit);

    // File browser listeners
    browseFilesBtn.addEventListener('click', openFileBrowser);
    closeBrowserModal.addEventListener('click', closeFileBrowser);
    cancelBrowserBtn.addEventListener('click', closeFileBrowser);
    selectFileBtn.addEventListener('click', selectBrowsedFile);

    // Source type toggle
    sourceTypeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            const cameraSection = document.getElementById('cameraSection');
            if (e.target.value === 'existing') {
                existingFileSection.style.display = 'block';
                uploadFileSection.style.display = 'none';
                cameraSection.style.display = 'none';
            } else if (e.target.value === 'upload') {
                existingFileSection.style.display = 'none';
                uploadFileSection.style.display = 'block';
                cameraSection.style.display = 'none';
            } else if (e.target.value === 'camera') {
                existingFileSection.style.display = 'none';
                uploadFileSection.style.display = 'none';
                cameraSection.style.display = 'block';
            }
        });
    });

    // Protocol recommendation
    const protocolSelect = document.getElementById('protocol');
    if (protocolSelect) {
        protocolSelect.addEventListener('change', updateProtocolRecommendation);
    }

    // Authentication toggle
    const enableAuthCheckbox = document.getElementById('enableAuth');
    const authSection = document.getElementById('authSection');
    if (enableAuthCheckbox && authSection) {
        enableAuthCheckbox.addEventListener('change', (e) => {
            authSection.style.display = e.target.checked ? 'grid' : 'none';
        });
    }

    // Advanced Options toggle
    const advancedToggle = document.getElementById('advancedToggle');
    const advancedContent = document.getElementById('advancedContent');
    if (advancedToggle && advancedContent) {
        advancedToggle.addEventListener('click', () => {
            advancedToggle.classList.toggle('active');
            advancedContent.classList.toggle('active');
        });
    }

    // Close modal on outside click
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModalDialog();
        }
        if (e.target === fileBrowserModal) {
            closeFileBrowser();
        }
        if (e.target === recordingsModal) {
            closeRecordingsModalDialog();
        }
    });
}

function openModal() {
    modal.style.display = 'block';
    loadMediaFiles();
}

function closeModalDialog() {
    modal.style.display = 'none';
    streamForm.reset();
    document.getElementById('uploadProgress').style.display = 'none';
}

function updateProtocolRecommendation() {
    const protocol = document.getElementById('protocol').value;
    const useCaseSpan = document.getElementById('protocolUseCase');

    const recommendations = {
        'rtsp': 'General streaming with low latency. Best for VLC, FFmpeg, and most media players.',
        'srt': 'Ultra-low latency over unreliable networks. Best for live streaming over the internet.',
        'rtmp': 'Traditional streaming protocol. Best for compatibility with older streaming services.'
    };

    if (useCaseSpan && recommendations[protocol]) {
        useCaseSpan.textContent = recommendations[protocol];
    }
}

async function loadMediaFiles() {
    try {
        const response = await fetch(`${API_BASE}/media/list`);
        const data = await response.json();

        const select = document.getElementById('existingFile');
        select.innerHTML = '';

        if (data.success && data.files.length > 0) {
            data.files.forEach(file => {
                const option = document.createElement('option');
                option.value = file;
                option.textContent = file;
                select.appendChild(option);
            });
        } else {
            select.innerHTML = '<option value="">No files available</option>';
        }
    } catch (error) {
        console.error('Error loading media files:', error);
        showNotification('Failed to load media files', 'error');
    }
}

async function loadStreams() {
    try {
        const response = await fetch(`${API_BASE}/streams/list`);
        const data = await response.json();

        if (data.success) {
            streams = {};
            data.streams.forEach(stream => {
                streams[stream.id] = stream;
            });
            renderStreams();
        }
    } catch (error) {
        console.error('Error loading streams:', error);
    }
}

function renderStreams() {
    streamsContainer.innerHTML = '';

    const streamList = Object.values(streams);

    if (streamList.length === 0) {
        noStreams.style.display = 'block';
        return;
    }

    noStreams.style.display = 'none';

    streamList.forEach(stream => {
        const card = createStreamCard(stream);
        streamsContainer.appendChild(card);
    });
}

function createStreamCard(stream) {
    const card = document.createElement('div');
    card.className = 'stream-card';
    card.id = `stream-${stream.id}`;

    const statusClass = `status-${stream.status}`;
    const protocolUpper = stream.protocol.toUpperCase();

    let actionsHTML = '';
    if (stream.status === 'running' || stream.status === 'starting') {
        actionsHTML = `
            <button class="btn btn-danger" onclick="stopStream('${stream.id}')">
                <span class="icon">⏹</span> Stop
            </button>
        `;
    }

    let errorHTML = '';
    if (stream.error) {
        errorHTML = `
            <div class="error-message">
                <strong>Error:</strong> ${escapeHtml(stream.error)}
            </div>
        `;
    }

    // Get health status indicator
    const metrics = stream.live_metrics || {};
    const healthStatus = metrics.health_status || 'unknown';
    const healthEmoji = healthStatus === 'healthy' ? '🟢' : healthStatus === 'waiting' ? '🟡' : '🔴';

    // Build metrics HTML
    let metricsHTML = '';
    if (stream.status === 'running' && metrics.source_ready !== undefined) {
        metricsHTML = `
            <div class="stream-metrics">
                <div class="metrics-header">
                    <strong>${healthEmoji} Live Metrics</strong>
                </div>
                <div class="metrics-grid">
                    <div class="metric-item">
                        <span class="metric-label">Viewers:</span>
                        <span class="metric-value">${metrics.viewers || 0}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Data Sent:</span>
                        <span class="metric-value">${metrics.bytes_sent || '0 B'}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Data Received:</span>
                        <span class="metric-value">${metrics.bytes_received || '0 B'}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Source:</span>
                        <span class="metric-value">${metrics.source_ready ? 'Ready' : 'Not Ready'}</span>
                    </div>
                </div>
            </div>
        `;
    }

    card.innerHTML = `
        <div class="stream-header">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <input type="checkbox" class="stream-checkbox" data-stream-id="${stream.id}" onchange="toggleStreamSelection('${stream.id}', this.checked)">
                <div>
                    <div class="stream-title">${escapeHtml(stream.name)}</div>
                    <span class="protocol-badge">${protocolUpper}</span>
                </div>
            </div>
            <span class="stream-status ${statusClass}">${stream.status}</span>
        </div>

        <div class="stream-info">
            <div class="info-row">
                <span class="info-label">File</span>
                <span class="info-value">${escapeHtml(stream.file)}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Bitrate</span>
                <span class="info-value">${stream.bitrate}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Resolution</span>
                <span class="info-value">${stream.resolution}</span>
            </div>
        </div>

        ${metricsHTML}

        ${stream.status === 'running' ? `
            <div class="stream-urls">
                <div class="url-section">
                    <strong>Available Playback URLs:</strong>
                </div>

                <div class="stream-url" onclick="copyStreamUrl('${stream.rtsp_url}')" title="Click to copy">
                    <span class="url-label">RTSP:</span>
                    <span class="url-value">${escapeHtml(stream.rtsp_url)}</span>
                </div>

                <div class="stream-url" onclick="copyStreamUrl('${stream.rtmp_url}')" title="Click to copy">
                    <span class="url-label">RTMP:</span>
                    <span class="url-value">${escapeHtml(stream.rtmp_url)}</span>
                </div>

                <div class="stream-url" onclick="copyStreamUrl('${stream.srt_url}')" title="Click to copy">
                    <span class="url-label">SRT:</span>
                    <span class="url-value">${escapeHtml(stream.srt_url)}</span>
                </div>

                <div class="stream-url" onclick="copyStreamUrl('${stream.hls_url}')" title="Click to copy">
                    <span class="url-label">HLS:</span>
                    <span class="url-value">${escapeHtml(stream.hls_url)}</span>
                </div>

                <div class="stream-url webrtc-url">
                    <span class="url-label">WebRTC:</span>
                    <a href="${escapeHtml(stream.webrtc_url)}" target="_blank" style="color: #3b82f6; text-decoration: none;">
                        ${escapeHtml(stream.webrtc_url)}
                    </a>
                </div>
            </div>
        ` : ''}

        ${errorHTML}

        <div class="stream-actions">
            ${actionsHTML}
            ${stream.status === 'running' ? `
                <button class="btn btn-success" onclick="window.open('${stream.webrtc_url}', '_blank')">
                    <span class="icon">🎥</span> Play WebRTC
                </button>
                <button class="btn btn-secondary" onclick="downloadOBSConfig('${stream.id}')">
                    <span class="icon">📥</span> OBS Config
                </button>
            ` : ''}
        </div>
    `;

    return card;
}

async function handleStreamSubmit(e) {
    e.preventDefault();

    const sourceType = document.querySelector('input[name="sourceType"]:checked').value;
    const streamName = document.getElementById('streamName').value.trim();
    const protocol = document.getElementById('protocol').value;
    const bitrate = document.getElementById('bitrate').value;
    const resolution = document.getElementById('resolution').value;
    const hwAccel = document.getElementById('hwAccel').value;
    const audioCodec = document.getElementById('audioCodec').value;
    const enableRecording = document.getElementById('enableRecording').checked;
    const enableAuth = document.getElementById('enableAuth').checked;
    const authUser = enableAuth ? document.getElementById('authUser').value.trim() : null;
    const authPass = enableAuth ? document.getElementById('authPass').value : null;

    let videoFile = null;
    let cameraUrl = null;

    if (sourceType === 'existing') {
        videoFile = document.getElementById('existingFile').value;
        if (!videoFile) {
            showNotification('Please select a video file', 'error');
            return;
        }
    } else if (sourceType === 'upload') {
        // Upload file first
        const fileInput = document.getElementById('uploadFile');
        if (!fileInput.files || fileInput.files.length === 0) {
            showNotification('Please select a file to upload', 'error');
            return;
        }

        videoFile = await uploadFile(fileInput.files[0]);
        if (!videoFile) {
            return; // Upload failed
        }
    } else if (sourceType === 'camera') {
        cameraUrl = document.getElementById('cameraUrl').value.trim();
        if (!cameraUrl) {
            showNotification('Please enter a camera RTSP URL', 'error');
            return;
        }
        if (!cameraUrl.startsWith('rtsp://') && !cameraUrl.startsWith('rtmp://')) {
            showNotification('Camera URL must start with rtsp:// or rtmp://', 'error');
            return;
        }
    }

    // Start the stream
    try {
        const response = await fetch(`${API_BASE}/streams/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file: videoFile,
                camera_url: cameraUrl,
                name: streamName,
                protocol: protocol,
                bitrate: bitrate,
                resolution: resolution || null,
                hw_accel: hwAccel || null,
                audio_codec: audioCodec || 'opus',
                enable_recording: enableRecording,
                auth_user: authUser,
                auth_pass: authPass
            })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Stream started successfully!', 'success');
            closeModalDialog();
            loadStreams();
        } else {
            showNotification(`Failed to start stream: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error starting stream:', error);
        showNotification('Failed to start stream', 'error');
    }
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const progressDiv = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('progressBarFill');
    const uploadStatus = document.getElementById('uploadStatus');

    progressDiv.style.display = 'block';
    progressBar.style.width = '0%';
    uploadStatus.textContent = 'Uploading...';

    try {
        const xhr = new XMLHttpRequest();

        return new Promise((resolve, reject) => {
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    progressBar.style.width = percentComplete + '%';
                    uploadStatus.textContent = `Uploading... ${Math.round(percentComplete)}%`;
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    const data = JSON.parse(xhr.responseText);
                    if (data.success) {
                        uploadStatus.textContent = 'Upload complete!';
                        showNotification('File uploaded successfully!', 'success');
                        resolve(data.filename);
                    } else {
                        uploadStatus.textContent = 'Upload failed';
                        showNotification(`Upload failed: ${data.error}`, 'error');
                        resolve(null);
                    }
                } else {
                    uploadStatus.textContent = 'Upload failed';
                    showNotification('Upload failed', 'error');
                    resolve(null);
                }
            });

            xhr.addEventListener('error', () => {
                uploadStatus.textContent = 'Upload failed';
                showNotification('Upload failed', 'error');
                resolve(null);
            });

            xhr.open('POST', `${API_BASE}/media/upload`);
            xhr.send(formData);
        });
    } catch (error) {
        console.error('Error uploading file:', error);
        showNotification('Failed to upload file', 'error');
        return null;
    }
}

async function stopStream(streamId) {
    if (!confirm('Are you sure you want to stop this stream?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/streams/stop/${streamId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Stream stopped', 'success');
            loadStreams();
        } else {
            showNotification(`Failed to stop stream: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error stopping stream:', error);
        showNotification('Failed to stop stream', 'error');
    }
}

async function stopAllStreams() {
    const streamCount = Object.keys(streams).length;
    if (streamCount === 0) {
        showNotification('No active streams to stop', 'info');
        return;
    }

    if (!confirm(`Are you sure you want to stop all ${streamCount} stream(s)?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/streams/stop-all`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showNotification(`Stopped ${data.stopped} stream(s)`, 'success');
            loadStreams();
        } else {
            showNotification(`Failed to stop streams: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error stopping streams:', error);
        showNotification('Failed to stop streams', 'error');
    }
}

function copyStreamUrl(url) {
    if (!url) return;

    navigator.clipboard.writeText(url).then(() => {
        showNotification('URL copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy URL:', err);
        showNotification('Failed to copy URL', 'error');
    });
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background-color: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 0.5rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        z-index: 10000;
        animation: slideInRight 0.3s ease-out;
        max-width: 400px;
        font-weight: 500;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Dark mode functionality
function initDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const isDarkMode = localStorage.getItem('darkMode') === 'true';

    if (isDarkMode) {
        document.body.classList.add('dark-mode');
        darkModeToggle.textContent = '☀️';
    }

    darkModeToggle.addEventListener('click', toggleDarkMode);
}

function toggleDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    document.body.classList.toggle('dark-mode');

    const isDarkMode = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDarkMode);
    darkModeToggle.textContent = isDarkMode ? '☀️' : '🌙';
}

// File Browser Functions
function openFileBrowser() {
    fileBrowserModal.style.display = 'block';
    currentBrowserPath = '/';
    selectedFilePath = null;
    selectFileBtn.disabled = true;
    browsePath('/');
}

function closeFileBrowser() {
    fileBrowserModal.style.display = 'none';
    selectedFilePath = null;
}

function selectBrowsedFile() {
    if (selectedFilePath) {
        // Extract just the filename from the full path
        const filename = selectedFilePath.split('/').pop();

        // Update the dropdown with the selected file path
        const select = document.getElementById('existingFile');

        // Check if option already exists
        let optionExists = false;
        for (let i = 0; i < select.options.length; i++) {
            if (select.options[i].value === selectedFilePath) {
                select.selectedIndex = i;
                optionExists = true;
                break;
            }
        }

        // If option doesn't exist, add it
        if (!optionExists) {
            const option = document.createElement('option');
            option.value = selectedFilePath;
            option.textContent = selectedFilePath;
            option.selected = true;
            select.appendChild(option);
        }

        closeFileBrowser();
        showNotification('File selected: ' + filename, 'success');
    }
}

async function browsePath(path) {
    try {
        fileList.innerHTML = '<div class="loading">Loading...</div>';

        const response = await fetch(`${API_BASE}/files/browse`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path: path })
        });

        const data = await response.json();

        if (data.success) {
            currentBrowserPath = data.path;
            renderBreadcrumb(data.path);
            renderFileList(data.items);
        } else {
            fileList.innerHTML = `<div class="error-message">${escapeHtml(data.error)}</div>`;
            showNotification(`Failed to browse: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error browsing files:', error);
        fileList.innerHTML = '<div class="error-message">Failed to load files</div>';
        showNotification('Failed to browse files', 'error');
    }
}

function renderBreadcrumb(path) {
    breadcrumb.innerHTML = '';

    const parts = path.split('/').filter(p => p);

    // Add root
    const rootItem = document.createElement('span');
    rootItem.className = 'breadcrumb-item';
    rootItem.textContent = 'Root';
    rootItem.dataset.path = '/';
    rootItem.addEventListener('click', () => browsePath('/'));
    breadcrumb.appendChild(rootItem);

    // Add path parts
    let currentPath = '';
    parts.forEach(part => {
        currentPath += '/' + part;
        const item = document.createElement('span');
        item.className = 'breadcrumb-item';
        item.textContent = part;
        item.dataset.path = currentPath;
        const pathToNavigate = currentPath;
        item.addEventListener('click', () => browsePath(pathToNavigate));
        breadcrumb.appendChild(item);
    });
}

function renderFileList(items) {
    fileList.innerHTML = '';

    if (items.length === 0) {
        fileList.innerHTML = '<div class="loading">No files or directories found</div>';
        return;
    }

    items.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'file-item';

        if (item.is_dir) {
            itemDiv.classList.add('directory');
            itemDiv.innerHTML = `
                <span class="file-item-icon">📁</span>
                <span class="file-item-name">${escapeHtml(item.name)}</span>
            `;
            itemDiv.addEventListener('click', () => browsePath(item.path));
        } else {
            itemDiv.innerHTML = `
                <span class="file-item-icon">🎬</span>
                <span class="file-item-name">${escapeHtml(item.name)}</span>
                <span class="file-item-size">${escapeHtml(item.size || '')}</span>
            `;
            itemDiv.addEventListener('click', () => selectFile(item.path, itemDiv));
        }

        fileList.appendChild(itemDiv);
    });
}

function selectFile(path, element) {
    // Remove previous selection
    document.querySelectorAll('.file-item.selected').forEach(el => {
        el.classList.remove('selected');
    });

    // Add selection to clicked element
    element.classList.add('selected');
    selectedFilePath = path;
    selectFileBtn.disabled = false;
}

// Bulk Operations
function toggleStreamSelection(streamId, isChecked) {
    if (isChecked) {
        selectedStreams.add(streamId);
    } else {
        selectedStreams.delete(streamId);
    }

    // Show/hide bulk actions button
    stopSelectedBtn.style.display = selectedStreams.size > 0 ? 'inline-block' : 'none';
}

async function stopSelectedStreams() {
    if (selectedStreams.size === 0) {
        showNotification('No streams selected', 'info');
        return;
    }

    if (!confirm(`Are you sure you want to stop ${selectedStreams.size} selected stream(s)?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/streams/bulk-stop`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                stream_ids: Array.from(selectedStreams)
            })
        });

        const data = await response.json();

        if (data.success) {
            showNotification(`Stopped ${data.stopped} stream(s)`, 'success');
            selectedStreams.clear();
            stopSelectedBtn.style.display = 'none';
            loadStreams();
        } else {
            showNotification(`Failed to stop streams: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error stopping selected streams:', error);
        showNotification('Failed to stop selected streams', 'error');
    }
}

// Recordings Modal
async function openRecordingsModal() {
    recordingsModal.style.display = 'block';
    await loadRecordings();
}

function closeRecordingsModalDialog() {
    recordingsModal.style.display = 'none';
}

async function loadRecordings() {
    try {
        const recordingsList = document.getElementById('recordingsList');
        recordingsList.innerHTML = '<div class="loading">Loading recordings...</div>';

        const response = await fetch(`${API_BASE}/recordings/list`);
        const data = await response.json();

        if (data.success) {
            renderRecordings(data.recordings);
        } else {
            recordingsList.innerHTML = `<div class="error-message">Failed to load recordings: ${data.error}</div>`;
        }
    } catch (error) {
        console.error('Error loading recordings:', error);
        document.getElementById('recordingsList').innerHTML = '<div class="error-message">Failed to load recordings</div>';
    }
}

function renderRecordings(recordings) {
    const recordingsList = document.getElementById('recordingsList');

    if (recordings.length === 0) {
        recordingsList.innerHTML = '<div class="loading">No recordings found</div>';
        return;
    }

    let html = '';
    recordings.forEach(streamRec => {
        html += `
            <div class="recording-group">
                <h3>${escapeHtml(streamRec.stream)} (${streamRec.count} recordings)</h3>
                <div class="recording-files">
        `;

        streamRec.files.forEach(file => {
            const date = new Date(file.modified * 1000).toLocaleString();
            html += `
                <div class="recording-file">
                    <div class="recording-info">
                        <strong>${escapeHtml(file.filename)}</strong>
                        <div style="font-size: 0.875rem; color: #6b7280; margin-top: 0.25rem;">
                            ${file.size} • ${date}
                        </div>
                    </div>
                    <div class="recording-actions">
                        <button class="btn btn-primary" onclick="downloadRecording('${file.path}')">
                            <span class="icon">📥</span> Download
                        </button>
                        <button class="btn btn-danger" onclick="deleteRecording('${file.path}')">
                            <span class="icon">🗑</span> Delete
                        </button>
                    </div>
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;
    });

    recordingsList.innerHTML = html;
}

function downloadRecording(filePath) {
    window.location.href = `${API_BASE}/recordings/download/${encodeURIComponent(filePath)}`;
    showNotification('Starting download...', 'success');
}

async function deleteRecording(filePath) {
    if (!confirm('Are you sure you want to delete this recording?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/recordings/delete/${encodeURIComponent(filePath)}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Recording deleted', 'success');
            loadRecordings();
        } else {
            showNotification(`Failed to delete recording: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error deleting recording:', error);
        showNotification('Failed to delete recording', 'error');
    }
}

// OBS Studio Integration
function downloadOBSConfig(streamId) {
    window.location.href = `${API_BASE}/obs/export/${streamId}`;
    showNotification('Downloading OBS configuration...', 'success');
}
