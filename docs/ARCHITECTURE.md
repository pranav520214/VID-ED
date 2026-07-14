"""
VID-ED AI - Comprehensive Architecture Documentation

A fully offline, MCP-based AI video editor powered by local Gemma.
"""

# Architecture Overview

## Core Philosophy

**Gemma is the DIRECTOR, not the editor.**

The AI (Gemma via Ollama) only creates editing plans. All actual video/audio manipulation
is performed by MCP (Model Context Protocol) servers. This separation ensures:

1. **Modularity**: Each MCP server handles a specific domain
2. **Reliability**: AI can't break things by generating invalid commands
3. **Extensibility**: New tools can be added without changing the AI
4. **Offline Operation**: Everything runs locally

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│  (Tauri + React 19 + TypeScript + Tailwind + shadcn/ui)         │
├─────────────────────────────────────────────────────────────────┤
│                         Backend API                              │
│                    (FastAPI + Python)                            │
├──────────────┬──────────────────────────────────────────────────┤
│  AI Director │              MCP Client                          │
│   (Gemma)    │         (Task Orchestrator)                      │
│              │                                                  │
│  • Parses    │  • Routes requests to MCP servers               │
│    requests  │  • Manages task dependencies                     │
│  • Creates   │  • Tracks progress                               │
│    plans     │  • Handles errors                                │
└──────────────┴──────────────────────────────────────────────────┘
         │
         │ Edit Plan (Task Graph)
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MCP Servers (Plugins)                        │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────┤
│  Video   │  Audio   │  Speech  │  Vision  │ Subtitle │ Effects │
│   MCP    │   MCP    │   MCP    │   MCP    │   MCP    │   MCP   │
├──────────┼──────────┼──────────┼──────────┼──────────┼─────────┤
│  Color   │  Export  │ Render   │ Timeline │          │         │
│   MCP    │   MCP    │   MCP    │   MCP    │          │         │
└──────────┴──────────┴──────────┴──────────┴──────────┴─────────┘
         │
         │ FFmpeg / OpenCV / ML Models
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Local Processing Layer                        │
│  • FFmpeg (video/audio processing)                              │
│  • OpenCV (computer vision)                                     │
│  • Whisper (speech-to-text)                                     │
│  • YOLOv11 (object detection)                                   │
│  • Demucs/RNNoise (audio enhancement)                           │
│  • SQLite (project storage)                                     │
└─────────────────────────────────────────────────────────────────┘
```

## MCP Server Types

### Video MCP
Handles all video manipulation operations.
- `create_project()` - Initialize new project
- `import_media()` - Load video/audio files
- `trim()`, `split()`, `cut()` - Basic editing
- `merge()` - Concatenate clips
- `crop()`, `zoom()`, `pan()` - Transformations
- `rotate()`, `speed()`, `freeze()`, `reverse()` - Effects
- `stabilize()` - Stabilization
- `render()` - Preview/final render

### Audio MCP
Audio processing and enhancement.
- `noise_removal()` - Remove background noise (RNNoise)
- `normalize()` - Level adjustment
- `duck_music()` - Sidechain compression
- `equalizer()` - EQ bands
- `compressor()` - Dynamic range
- `music_detection()` - Identify music segments
- `beat_detection()` - Find transients/beats

### Speech MCP
Speech analysis and transcription.
- `speech_to_text()` - Whisper transcription
- `speaker_detection()` - Identify speakers
- `translate()` - Translation
- `subtitle_generation()` - Create SRT/VTT
- `keyword_detection()` - Find keywords
- `remove_silence()` - Detect/cut silence

### Vision MCP
Computer vision operations.
- `object_detection()` - YOLOv11
- `scene_detection()` - Shot boundaries
- `face_tracking()` - Track faces
- `person_tracking()` - Track people
- `background_removal()` - RVM/MODNet
- `auto_reframe()` - Smart cropping
- `ocr()` - Text extraction
- `emotion_detection()` - Facial analysis

### Subtitle MCP
Caption generation and styling.
- Generate animated captions
- Word-level timing
- Platform styles (TikTok, Instagram, YouTube)
- Multi-language support
- Auto-translation

### Effects MCP
Visual effects library.
- Lens blur, glow, film grain
- Motion blur, transitions
- Camera shake, flash effects
- Whip pan, zoom effects
- Light leaks, chromatic aberration

### Color MCP
Color grading tools.
- White balance, exposure
- Contrast, saturation
- LUT application
- Color matching
- HDR tone mapping
- Skin tone correction

### Export MCP
Platform-specific exports.
- Resolutions: 1080p, 1440p, 4K, 8K
- Platforms: Instagram, TikTok, YouTube, Facebook
- Codecs: H264, HEVC, AV1

### Render MCP
Final rendering pipeline.
- Proxy generation
- Background rendering
- Progress tracking
- Queue management

### Timeline MCP
Timeline management.
- Track operations
- Clip positioning
- Snapping, alignment
- Ripple delete
- Undo/redo stack

## Data Flow Example

**User Request:** "Remove all silences and add subtitles"

1. **UI** → Sends request to Backend API
2. **Backend** → Forwards to AI Director
3. **AI Director** → Generates Edit Plan:
   ```json
   {
     "plan_id": "plan-123",
     "tasks": [
       {
         "id": "task-1",
         "tool_name": "remove_silence",
         "server_type": "speech",
         "parameters": {"audio_path": "/path/to/audio.mp3"},
         "dependencies": []
       },
       {
         "id": "task-2",
         "tool_name": "subtitle_generation",
         "server_type": "speech",
         "parameters": {"audio_path": "/path/to/audio.mp3"},
         "dependencies": []
       },
       {
         "id": "task-3",
         "tool_name": "cut",
         "server_type": "video",
         "parameters": {"clip_id": "main", "segments": "${task-1.result}"},
         "dependencies": ["task-1"]
       },
       {
         "id": "task-4",
         "tool_name": "burn_subtitles",
         "server_type": "video",
         "parameters": {"clip_id": "main", "subtitle_file": "${task-2.result}"},
         "dependencies": ["task-2", "task-3"]
       }
     ]
   }
   ```
4. **MCP Client** → Executes tasks respecting dependencies
5. **Speech MCP** → Runs `remove_silence()` and `subtitle_generation()` in parallel
6. **Video MCP** → Waits for speech tasks, then executes `cut()` and `burn_subtitles()`
7. **UI** → Shows progress, displays final result

## Project Structure

```
vid-ed-ai/
├── apps/
│   └── desktop/              # Tauri desktop app
├── backend/
│   ├── agents/               # AI Director
│   │   └── ai_director.py
│   ├── mcp_servers/          # Built-in MCP servers
│   ├── video_processing/     # FFmpeg wrappers
│   ├── audio_analysis/       # Librosa, audio tools
│   ├── ai_logic/             # ML model loaders
│   └── utils/                # Shared utilities
├── packages/
│   ├── ui/                   # Shared UI components
│   ├── timeline/             # Timeline component
│   └── mcp-client/           # MCP protocol & client
│       ├── protocol.py       # Type definitions
│       └── client.py         # Orchestration
├── plugins/
│   └── servers/              # MCP server plugins
│       ├── video-mcp/
│       ├── audio-mcp/
│       ├── speech-mcp/
│       ├── vision-mcp/
│       ├── subtitle-mcp/
│       ├── effects-mcp/
│       ├── color-mcp/
│       └── render-mcp/
├── storage/
│   ├── database/             # SQLite schemas
│   └── assets/               # Media assets
├── frontend/
│   ├── src/                  # React source
│   └── src-tauri/            # Tauri Rust code
├── tests/                    # Test suites
└── docs/                     # Documentation
```

## Plugin System

MCP servers are designed as plugins. Developers can create new servers without
modifying core application code.

### Creating a Plugin

```python
# my-custom-mcp/server.py
from packages.mcp_client.protocol import MCPServer, MCPServerType, MCPTool, MCPResponse

class MyCustomMCPServer(MCPServer):
    @property
    def server_type(self) -> MCPServerType:
        return MCPServerType("custom")
    
    @property
    def tools(self) -> list[MCPTool]:
        return [
            MCPTool(
                name="my_custom_tool",
                description="Does something cool",
                parameters={"param1": {"type": "string", "required": True}},
                server_type=self.server_type,
            )
        ]
    
    async def execute_tool(self, tool_name: str, parameters: dict) -> MCPResponse:
        # Implementation
        pass
    
    async def cancel_task(self, request_id: str) -> bool:
        return False
```

Register plugin in main application:
```python
from my_custom_mcp import MyCustomMCPServer

mcp_client.register_server(MyCustomMCPServer())
```

## AI Model Configuration

### Default Models (Optimized for 4GB VRAM)

| Component | Model | Size | Purpose |
|-----------|-------|------|---------|
| LLM Director | Gemma 3 4B Instruct | ~2.5GB (Q4_K_M) | Plan generation |
| Speech-to-Text | Whisper Tiny | 39 MB | Transcription |
| Object Detection | YOLOv11 Nano | ~2 MB | Highlight ID |
| Audio Separation | Demucs v4 | ~150 MB | Music/vocal sep |
| Face Detection | MediaPipe | ~10 MB | Face tracking |
| Background Removal | RVM (Tiny) | ~50 MB | Green screen |

### Hardware Detection

Application detects available resources:
```python
def detect_hardware():
    ram = psutil.virtual_memory().total / (1024 ** 3)
    vram = get_gpu_vram()  # CUDA/Metal query
    
    if vram >= 8:
        return "high"  # Use larger models
    elif vram >= 4:
        return "medium"  # Default models
    else:
        return "low"  # CPU-only or tiny models
```

## Performance Optimizations

1. **Lazy Loading**: ML models loaded on-demand
2. **Caching**: Analysis results cached per media file
3. **Proxy Editing**: Low-res proxies for timeline
4. **Background Queues**: Non-blocking render jobs
5. **GPU Acceleration**: CUDA/Metal when available
6. **Multithreading**: Parallel task execution
7. **Incremental Processing**: Resume interrupted renders

## Testing Strategy

### Unit Tests
Test individual functions:
```python
def test_silence_detection():
    audio = generate_test_audio(with_silence=True)
    segments = detect_silence(audio)
    assert len(segments) > 0
```

### Integration Tests
Test module interactions:
```python
async def test_ai_to_mcp_flow():
    director = AIDirector()
    plan = await director.generate_plan("Remove silence")
    results = await mcp_client.execute_plan(plan)
    assert all(r.success for r in results.values())
```

### E2E Tests
Full user workflows:
```python
def test_full_edit_workflow():
    # Import media
    # Send AI request
    # Wait for render
    # Verify output
```

## Future Roadmap

### Phase 1: Foundation (Current)
- [x] MCP protocol definition
- [x] Core MCP servers (Video, Audio, Speech, Vision)
- [x] AI Director with Gemma integration
- [x] Basic Tauri + React UI skeleton

### Phase 2: Core Features
- [ ] Complete all MCP server implementations
- [ ] Timeline component with OTIO
- [ ] Real-time preview system
- [ ] Plugin marketplace

### Phase 3: Advanced AI
- [ ] Multi-agent workflows
- [ ] Auto-highlight detection
- [ ] Smart B-roll insertion
- [ ] Voice-controlled editing

### Phase 4: Professional Features
- [ ] Collaborative editing
- [ ] Cloud sync (optional)
- [ ] DaVinci Resolve integration
- [ ] Mobile companion app

## Contributing

See docs/BUILD_BIBLE.md for coding standards and contribution guidelines.

## License

MIT License - See LICENSE file for details.
