# EditFlow AI - Local AI-Powered Video Editor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)]()

A free, local, AI-powered video editor designed to run on mid-range PCs (4GB VRAM minimum).

## 🎯 Goal

EditFlow AI enables smart beginners, students, and indie developers to create professional video edits using natural language commands. All processing happens locally on your machine—no data leaves your PC unless you explicitly choose cloud features.

## ✨ Key Features

- **AI Director Agent**: Control edits with natural language ("Remove silence", "Add subtitles", "Cut to music beats")
- **Local-First Processing**: All heavy computation stays on your machine
- **Lightweight Models**: Optimized for mid-range hardware (Whisper Tiny/Base, YOLO Nano)
- **FFmpeg-Powered**: Professional-grade video processing under the hood
- **Premiere Pro Integration**: Export edit plans to Adobe Premiere (coming soon)

## 📋 Milestone Roadmap

### Phase 1: Foundation & Setup (Milestones 1–5)
- [x] Initialize GitHub Repo & Python Environment
- [ ] Set Up Tauri + React Frontend Skeleton
- [ ] Set Up FastAPI Backend Skeleton
- [ ] Connect Frontend to Backend (Hello World)
- [ ] Basic File Picker UI

### Phase 2: Core Video Processing with FFmpeg (Milestones 6–12)
- [ ] Install & Verify FFmpeg
- [ ] Load Video Metadata (Duration, Resolution)
- [ ] Extract Audio from Video
- [ ] Extract Frames from Video
- [ ] Basic Video Trimming (Start/End)
- [ ] Concatenate Two Video Clips
- [ ] Export Final Video

### Phase 3: Audio Analysis Engine (Milestones 13–20)
- [ ] Install Librosa & OpenCV
- [ ] Generate Audio Waveform Data
- [ ] Detect Silence Segments
- [ ] Remove Silence from Audio
- [ ] Sync Silence Removal to Video
- [ ] Detect Loudness Peaks
- [ ] Normalize Audio Volume
- [ ] Add Background Music Track

### Phase 4: AI Vision & Speech (Milestones 21–30)
- [ ] Install Whisper (Tiny Model)
- [ ] Transcribe Audio to Text
- [ ] Generate Timestamped Subtitles (SRT)
- [ ] Burn Subtitles into Video
- [ ] Install ONNX Runtime
- [ ] Convert Whisper to ONNX for Speed
- [ ] Scene Detection using OpenCV
- [ ] Identify Key Frames (Highlights)
- [ ] Basic Object Detection (YOLO Nano)
- [ ] Filter Highlights by Object Presence

### Phase 5: The AI Director Agent (Milestones 31–40)
- [ ] Set Up Local LLM (Ollama + Llama3.2-3B)
- [ ] Create Prompt Parser
- [ ] Map Natural Language to Editing Actions
- [ ] Create "Edit Plan" JSON Structure
- [ ] Implement "Remove Silence" Command
- [ ] Implement "Add Subtitles" Command
- [ ] Implement "Cut to Music Beat" Command
- [ ] Implement "Color Correct" Command
- [ ] Validate Edit Plans
- [ ] Execute Multi-Step Edit Plans

### Phase 6: Advanced Editing Features (Milestones 41–50)
- [ ] Auto-Zoom on Highlights
- [ ] Add Simple Transitions (Fade/Crossfade)
- [ ] Add Sound Effects Library
- [ ] Sync SFX to Visual Events
- [ ] Vertical Crop for Shorts/Reels
- [ ] Auto-Reframe for Vertical Video
- [ ] Generate Thumbnail from Best Frame
- [ ] Batch Process Multiple Clips
- [ ] Preview Generation (Low-Res Proxy)
- [ ] Final High-Res Export

### Phase 7: Premiere Pro Integration (Milestones 51–55)
- [ ] Research Adobe ExtendScript API
- [ ] Create "Send to Premiere" Button
- [ ] Generate JSX Script from Edit Plan
- [ ] Launch Premiere via Python
- [ ] Execute JSX Script in Premiere

### Phase 8: Polish & Performance (Milestones 56–65)
- [ ] GPU Acceleration Check (CUDA/Metal)
- [ ] Fallback to CPU if GPU Fails
- [ ] Progress Bar for Long Tasks
- [ ] Cancel Button for Operations
- [ ] Error Logging System
- [ ] User Settings (Model Size, Output Format)
- [ ] Dark Mode UI
- [ ] Keyboard Shortcuts
- [ ] Onboarding Tutorial Overlay
- [ ] Offline Mode Verification

### Phase 9: Testing & Documentation (Milestones 66–70)
- [ ] Write Unit Tests for Audio Engine
- [ ] Write Unit Tests for AI Agent
- [ ] End-to-End User Flow Test
- [ ] Create User Documentation (Markdown)
- [ ] Release v1.0 Beta

## 🏗️ Architecture

```
editflow-ai/
├── backend/
│   ├── ai_logic/          # AI models (Whisper, YOLO, LLM)
│   ├── audio_analysis/    # Librosa, waveform, silence detection
│   ├── video_processing/  # FFmpeg wrappers, frame extraction
│   ├── agents/            # AI Director Agent logic
│   └── utils/             # Shared utilities
├── frontend/
│   ├── src/               # React + Tauri source code
│   └── public/            # Static assets
├── tests/
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
└── docs/                  # Documentation
```

## 📜 Repository Constitution

### Coding Rules
1. **No Hallucinations**: Never import a library that doesn't exist. Verify on PyPI first.
2. **Type Safety**: Use Python type hints everywhere (`def func(name: str) -> int:`)
3. **Small Functions**: One function does one thing (<50 lines)
4. **Comments**: Explain *why*, not *what* (the code shows what)
5. **Error Handling**: Catch errors and show friendly messages to users

### Architecture Rules
- **Modular Design**: AI logic, UI logic, and Video Processing in separate folders
- **Local First**: All heavy processing on user's computer
- **Lightweight Defaults**: Assume 4GB VRAM; use small models by default

### Testing Standards
- **Unit Tests**: Test every individual function
- **Integration Tests**: Test module interactions
- **Manual QA**: Run and try to break before marking milestones complete

## 🚀 Getting Started

### Prerequisites

| Requirement | Version | Installation Link |
|-------------|---------|-------------------|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| FFmpeg | Latest | [ffmpeg.org](https://ffmpeg.org/download.html) |
| Git | Latest | [git-scm.com](https://git-scm.com/) |

**Verify FFmpeg installation:**
```bash
ffmpeg -version
```

### Step-by-Step Installation

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd editflow-ai
```

#### 2. Set Up Python Virtual Environment

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

#### 3. Install Backend Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install project dependencies (using pyproject.toml)
pip install -e .
```

#### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

#### 5. Verify Installation

```bash
# Run backend tests
pytest tests/unit/

# Start the development server (once implemented)
python -m uvicorn backend.main:app --reload
```

## 🛠️ Development Workflow

### Branch Naming Convention
```
feat/<feature-name>     # New features
fix/<bug-description>   # Bug fixes
docs/<update-type>      # Documentation changes
test/<test-addition>    # Adding tests
```

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Examples:**
- `feat(audio): Add silence detection using Librosa`
- `fix(video): Resolve frame extraction offset bug`
- `docs(readme): Update installation instructions`

### Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# With coverage
pytest --cov=backend tests/
```

## 📦 Default Models (Optimized for 4GB VRAM)

| Component | Model | Size | Purpose |
|-----------|-------|------|---------|
| Speech-to-Text | Whisper Tiny | 39 MB | Audio transcription |
| Object Detection | YOLO Nano | ~2 MB | Highlight identification |
| LLM Agent | Llama3.2-3B | ~2 GB | Natural language parsing |

## 🔧 Configuration

Create a `.env` file in the root directory:

```env
# Model settings
WHISPER_MODEL=tiny
LLM_MODEL=llama3.2:3b
GPU_ACCELERATION=false

# Output settings
OUTPUT_FORMAT=mp4
OUTPUT_RESOLUTION=1080p
```

## 🐛 Troubleshooting

### Common Issues

**FFmpeg not found:**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows (with Chocolatey)
choco install ffmpeg
```

**Insufficient VRAM:**
- Set `GPU_ACCELERATION=false` in `.env`
- Use smaller model variants (Whisper Tiny instead of Base)

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

Please read [docs/BUILD_BIBLE.md](docs/BUILD_BIBLE.md) for detailed coding standards and contribution guidelines.

## 📬 Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/editflow-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/editflow-ai/discussions)

---

**Built with ❤️ for creators everywhere**