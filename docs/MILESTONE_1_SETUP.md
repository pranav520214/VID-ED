# EditFlow AI - Milestone 1 Setup Guide

## Overview

This guide walks you through setting up the Python environment for EditFlow AI (Milestone 1).

## Prerequisites Verification

Before starting, verify you have the required software installed:

```bash
# Check Python version (must be 3.10 or higher)
python --version
# OR on some systems:
python3 --version

# Check Git
git --version

# Check FFmpeg (required for video processing)
ffmpeg -version
```

If any of these are missing, install them first:
- **Python**: https://www.python.org/downloads/
- **Git**: https://git-scm.com/
- **FFmpeg**: https://ffmpeg.org/download.html

## Step-by-Step Virtual Environment Setup

### Step 1: Navigate to Project Directory

```bash
cd /path/to/editflow-ai
```

### Step 2: Create Virtual Environment

A virtual environment isolates project dependencies from your system Python packages.

**On macOS/Linux:**
```bash
python -m venv venv
```

**On Windows:**
```bash
python -m venv venv
```

This creates a `venv/` directory containing the isolated Python installation.

### Step 3: Activate the Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```bash
venv\Scripts\activate.bat
```

**Verification:** After activation, you should see `(venv)` in your terminal prompt:
```bash
(venv) user@machine:~/editflow-ai$
```

### Step 4: Upgrade pip

Always upgrade pip to the latest version before installing dependencies:

```bash
pip install --upgrade pip
```

### Step 5: Install Project Dependencies

Install all required packages using the `pyproject.toml` file:

```bash
pip install -e .
```

The `-e` flag installs the package in "editable" mode, meaning changes to your code are immediately reflected without reinstalling.

**What gets installed:**
- `ffmpeg-python` - Python bindings for FFmpeg
- `librosa` - Audio analysis library
- `opencv-python-headless` - Computer vision
- `openai-whisper` - Speech-to-text AI
- `onnxruntime` - Optimized AI inference
- `fastapi` + `uvicorn` - Backend API server
- `pydantic` - Data validation
- `pytest` - Testing framework
- And more...

### Step 6: Verify Installation

Test that key packages are installed correctly:

```bash
# Check installed packages
pip list | grep -E "(ffmpeg|librosa|opencv|whisper|fastapi)"

# Test Python imports
python -c "import ffmpeg; import librosa; import cv2; import fastapi; print('✅ All core packages imported successfully!')"
```

### Step 7: Run Initial Tests (Optional)

Verify the testing framework works:

```bash
pytest tests/unit/ -v
```

## Troubleshooting

### Issue: "python: command not found"

**Solution:** 
- On macOS/Linux, try `python3` instead of `python`
- On Windows, ensure Python is added to PATH during installation

### Issue: "Permission denied" when creating venv

**Solution:**
```bash
# Make sure you're in a directory where you have write permissions
cd ~/projects/editflow-ai  # Use a directory in your home folder
```

### Issue: FFmpeg not found errors

**Solution:** Install FFmpeg system-wide:

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Windows (with Chocolatey):**
```bash
choco install ffmpeg
```

**Windows (manual):**
1. Download from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to System PATH

### Issue: Slow installation or timeouts

**Solution:** Use a PyPI mirror:

```bash
pip install -e . -i https://pypi.org/simple/
```

Or install packages individually to identify bottlenecks.

### Issue: GPU support needed

**Solution:** Install with GPU extras:

```bash
pip install -e ".[gpu]"
```

Note: Requires NVIDIA GPU with CUDA support.

## Next Steps

After completing this setup:

1. ✅ Milestone 1 Complete: Python Environment Initialized
2. ➡️ Proceed to Milestone 2: Set Up Tauri + React Frontend Skeleton

## Quick Reference Commands

```bash
# Activate environment (always do this before working on the project)
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Deactivate environment (when done)
deactivate

# List installed packages
pip list

# Check for outdated packages
pip list --outdated

# Update a specific package
pip install --upgrade <package-name>

# Freeze dependencies (for documentation)
pip freeze > requirements.txt
```

## Project Structure Reminder

```
editflow-ai/
├── venv/                 # Virtual environment (DO NOT COMMIT)
├── backend/              # Python backend code
├── frontend/             # React + Tauri frontend
├── tests/                # Test files
├── docs/                 # Documentation
├── pyproject.toml        # Project configuration
├── README.md             # This file
└── .gitignore            # Git ignore rules
```

---

**Need Help?** Check the main [README.md](../README.md) or open an issue on GitHub.
