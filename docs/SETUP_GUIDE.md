# VID-ED AI - Setup Guide

## Quick Start

This guide will help you set up and run VID-ED AI on your local machine.

## Prerequisites

### Required Software

| Software | Version | Installation Link |
|----------|---------|-------------------|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| FFmpeg | Latest | [ffmpeg.org](https://ffmpeg.org/download.html) |
| Git | Latest | [git-scm.com](https://git-scm.com/) |
| Ollama | Latest | [ollama.ai](https://ollama.ai/) |

### Verify FFmpeg Installation

```bash
ffmpeg -version
```

### Install Ollama and Gemma Model

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Install Ollama (Windows)
# Download from https://ollama.ai/download

# Pull Gemma 3 4B Instruct model
ollama pull gemma3:4b-instruct

# Verify installation
ollama run gemma3:4b-instruct "Hello"
```

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd vid-ed-ai
```

### 2. Set Up Python Virtual Environment

**On macOS/Linux:**
```bash
# Create virtual environment
python -m venv venv

# Activate the environment
source venv/bin/activate
```

**On Windows:**
```bash
# Create virtual environment
python -m venv venv

# Activate the environment
venv\Scripts\activate
```

**Verify activation:** You should see `(venv)` in your terminal prompt.

### 3. Install Backend Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install project dependencies
pip install -e .

# Install optional GPU acceleration (NVIDIA only)
pip install -e ".[gpu]"

# Install development tools
pip install -e ".[dev]"
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Configure Environment

Create a `.env` file in the root directory:

```env
# Model settings
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=gemma3:4b-instruct
WHISPER_MODEL=tiny

# Hardware settings
GPU_ACCELERATION=true
VRAM_LIMIT=4

# Output settings
OUTPUT_FORMAT=mp4
OUTPUT_RESOLUTION=1080p
OUTPUT_FPS=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=vid-ed-ai.log
```

### 6. Verify Installation

```bash
# Run backend tests
pytest tests/unit/ -v

# Check Ollama connection
python -c "import httpx; print(httpx.get('http://localhost:11434/api/tags').json())"
```

## Running the Application

### Development Mode

**Terminal 1 - Backend API:**
```bash
# Activate virtual environment if not already active
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start FastAPI backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend (Tauri dev):**
```bash
cd frontend
npm run tauri dev
```

### Production Build

```bash
cd frontend
npm run tauri build
```

The built application will be in `frontend/src-tauri/target/release/`.

## Hardware Requirements

### Minimum Requirements

- **CPU:** Intel i5 / AMD Ryzen 5 (8th gen or newer)
- **RAM:** 8 GB
- **VRAM:** 4 GB (for GPU acceleration)
- **Storage:** 10 GB free space
- **OS:** Windows 10, macOS 11+, or Linux (Ubuntu 20.04+)

### Recommended Requirements

- **CPU:** Intel i7 / AMD Ryzen 7 (10th gen or newer)
- **RAM:** 16 GB
- **VRAM:** 8 GB (NVIDIA RTX 3060 or better)
- **Storage:** 50 GB SSD
- **OS:** Windows 11, macOS 13+, or Linux (Ubuntu 22.04+)

### Model Recommendations by Hardware

| VRAM | LLM Model | Whisper | YOLO | Notes |
|------|-----------|---------|------|-------|
| < 4GB | Gemma 2B | Tiny | Nano | CPU-only fallback |
| 4-6GB | Gemma 4B Q4 | Tiny/Base | Nano | Default config |
| 6-8GB | Gemma 4B Q8 | Small | Small | Good balance |
| 8+GB | Gemma 9B | Medium | Medium | Best quality |

## Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
# macOS/Linux
launchctl stop ai.ollama.ollama
launchctl start ai.ollama.ollama

# Windows
# Restart Ollama from system tray

# Test connection
curl http://localhost:11434/api/tags
```

### FFmpeg Not Found

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows (with Chocolatey)
choco install ffmpeg

# Windows (manual)
# Download from https://ffmpeg.org/download.html
# Add to PATH
```

### Insufficient VRAM

If you get CUDA out-of-memory errors:

1. Set `GPU_ACCELERATION=false` in `.env`
2. Use smaller models in Settings
3. Close other GPU-intensive applications

```env
GPU_ACCELERATION=false
LLM_MODEL=gemma3:2b-instruct
WHISPER_MODEL=tiny
```

### Python Import Errors

```bash
# Reinstall dependencies
pip uninstall editflow-ai
pip install -e . --force-reinstall

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### Tauri Build Issues

```bash
# Update Tauri CLI
cd frontend
npm update @tauri-apps/cli

# Clean and rebuild
rm -rf src-tauri/target
npm run tauri build
```

## Next Steps

After successful installation:

1. **Read the Documentation:** See `docs/ARCHITECTURE.md` for system design
2. **Try Example Edits:** Import a video and test natural language commands
3. **Explore MCP Servers:** Check `plugins/servers/` for available tools
4. **Join the Community:** Visit GitHub Discussions for help and ideas

## Support

- **Documentation:** `/docs` folder
- **Issues:** [GitHub Issues](https://github.com/yourusername/vid-ed-ai/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/vid-ed-ai/discussions)

## License

MIT License - See LICENSE file for details.
