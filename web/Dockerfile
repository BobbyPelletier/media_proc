FROM python:3.11-slim

# Install FFmpeg and networking tools
RUN apt-get update && \
    apt-get install -y ffmpeg iputils-ping netcat-traditional curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directories
RUN mkdir -p /streams /recordings

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
