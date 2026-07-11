# VID-ED X Architecture Documentation

## Overview

VID-ED X is an AI-native universal video editing platform designed as an extensible operating system for video creation. It functions as:

1. **A standalone AI video editor**
2. **An AI copilot for existing editors**
3. **An extensible MCP (Model Context Protocol) platform**
4. **A plugin ecosystem for creative AI workflows**

---

## Core Architecture Principles

### 1. Local-First AI
- **Primary Model**: Gemma 3 via Ollama (local execution)
- **Responsibility**: Planning, workflow reasoning, tool selection
- **Never edits media directly**: Creates structured execution plans only

### 2. Cloud AI (Optional)
- Unified provider abstraction layer
- Support for Google Gemini, OpenAI, and additional providers
- Graceful fallback between providers
- User-configurable provider ordering

### 3. MCP-Based Communication
- All specialized tools communicate through Model Context Protocol
- No direct dependencies between MCP servers
- Loose coupling enables independent evolution

### 4. Editor Agnosticism
- Universal project format independent of any editor
- Adapter pattern for editor integrations
- Supports Premiere Pro, Clipchamp, OpenShot, and future editors

---

## Project Structure

```
vid-ed-x/
├── apps/                          # Application entry points
│   ├── desktop/                   # Tauri-based desktop app
│   └── web/                       # Web application
│
├── packages/                      # Shared libraries
│   ├── core/                      # Core types, utilities, project format
│   ├── timeline/                  # Timeline data structures and operations
│   ├── mcp-client/                # MCP client implementation
│   ├── ui/                        # Shared UI components
│   ├── providers/                 # AI provider abstraction layer
│   ├── plugins/                   # Plugin system
│   └── integrations/              # Editor adapters
│       ├── clipchamp/
│       ├── premiere/
│       └── openshot/
│
├── servers/                       # MCP Servers
│   ├── video-mcp/                 # Video processing tools
│   ├── audio-mcp/                 # Audio processing tools
│   ├── vision-mcp/                # Computer vision tools
│   ├── speech-mcp/                # Speech recognition/synthesis
│   ├── subtitle-mcp/              # Subtitle generation
│   ├── filesystem-mcp/            # File operations
│   ├── timeline-mcp/              # Timeline manipulation
│   ├── effects-mcp/               # Visual effects
│   ├── export-mcp/                # Export/rendering
│   ├── plugin-mcp/                # Plugin management
│   └── provider-mcp/              # AI provider interface
│
├── storage/                       # Data persistence
│   └── database/                  # SQLite/IndexedDB schemas
│
├── tests/                         # Test suites
│   ├── unit/
│   └── integration/
│
└── docs/                          # Documentation
```

---

## Core Modules

### @vid-ed-x/core

The foundation module containing:

- **Types**: Comprehensive TypeScript type definitions
- **Project Format**: Universal editor-independent project representation
- **Timeline**: Timeline data structures and utilities
- **Utilities**: Common helper functions

Key exports:
```typescript
// Types
MediaType, VideoCodec, AudioCodec, ResolutionPreset
AspectRatio, FrameRate, ExportFormat
AIProviderType, AIProviderConfig, AICapabilities
AgentType, AgentStatus, PluginManifest, EditorType

// Project Format
Project, Sequence, Track, BaseClip, VideoClip, AudioClip
TextClip, TransitionClip, EffectInstance, Marker

// Utilities
generateId, deepClone, debounce, throttle
formatBytes, formatDuration, secondsToTimecode
```

### @vid-ed-x/providers

Unified AI provider abstraction supporting:

- **Local Models**: Gemma 3, Llama via Ollama
- **Cloud Providers**: Google Gemini, OpenAI, Anthropic
- **Capabilities**: Text, image, video, audio generation/processing

Key classes:
```typescript
ProviderManager      // Central provider orchestration
IAIProvider          // Provider interface
GenerationResponse   // Standardized response format
```

Features:
- Automatic failover between providers
- Usage monitoring and statistics
- Connection testing
- Latency tracking

### @vid-ed-x/mcp-client

Model Context Protocol client for tool communication:

```typescript
MCPClient           // Main client class
ToolRegistry        // Centralized tool discovery
MCPServerType       // Server type enumeration
```

Supported MCP Servers:
| Server | Purpose |
|--------|---------|
| video-mcp | Video trimming, concatenation, encoding |
| audio-mcp | Audio analysis, mixing, enhancement |
| vision-mcp | Scene detection, object recognition |
| speech-mcp | Transcription, voice synthesis |
| subtitle-mcp | Caption generation, styling |
| filesystem-mcp | File I/O, media import |
| timeline-mcp | Timeline operations |
| effects-mcp | Visual effects application |
| export-mcp | Render queue management |
| plugin-mcp | Plugin lifecycle |
| provider-mcp | AI model access |

---

## AI Architecture

### Agent System

Specialized AI agents for different tasks:

| Agent | Responsibility |
|-------|---------------|
| Director Agent | Creates editing strategy from natural language |
| Editor Agent | Executes timeline modifications |
| Subtitle Agent | Generates and syncs captions |
| Colorist Agent | Performs color grading |
| Audio Engineer | Enhances audio quality |
| Motion Designer | Creates graphics and animations |
| Publishing Agent | Optimizes exports for platforms |
| Research Agent | Finds stock assets and references |

### Workflow Example

```
User: "Remove every awkward pause and add subtitles"

1. Director Agent parses intent
2. Creates execution plan:
   - Detect silence segments (audio-mcp)
   - Generate edit list for removal (timeline-mcp)
   - Transcribe speech (speech-mcp)
   - Generate subtitle file (subtitle-mcp)
3. Presents plan to user for confirmation
4. Executes approved actions through MCP tools
5. Reports progress and completion
```

---

## Universal Project Format

The project format is editor-agnostic, enabling interoperability:

```typescript
interface Project {
  id: ID;
  name: string;
  sequences: Sequence[];
  mediaLibrary: MediaItem[];
  assets: Asset[];
  exportPresets: ExportPreset[];
  settings: ProjectSettings;
}

interface Sequence {
  id: ID;
  name: string;
  width: number;
  height: number;
  frameRate: number;
  tracks: Track[];
}

interface Track {
  id: ID;
  type: TrackType;
  clips: BaseClip[];
}
```

### Editor Adapters

Each editor integration implements:

```typescript
interface EditorAdapter {
  type: EditorType;
  connect(): Promise<void>;
  importProject(project: Project): Promise<void>;
  exportProject(): Promise<Project>;
  syncTimeline(): Promise<void>;
  disconnect(): Promise<void>;
}
```

---

## Plugin System

Plugins extend VID-ED X capabilities:

```typescript
interface PluginManifest {
  id: ID;
  name: string;
  version: string;
  entryPoint: string;
  capabilities: string[];
  permissions: string[];
}
```

Plugin categories:
- Transitions
- Effects
- AI Models
- Exporters
- Templates
- Stock Providers

Security:
- Sandboxed execution
- Permission-based access
- Version management

---

## Technology Stack

### Frontend
- **React 19** with TypeScript
- **Tauri v2** for desktop runtime
- **Tailwind CSS** for styling
- **shadcn/ui** for components
- **Vite** for bundling

### Backend
- **Rust** (Tauri commands)
- **Python** (video processing, AI)
- **FastAPI** (optional HTTP API)
- **FFmpeg** (media processing)

### AI/ML
- **Ollama** (local model runtime)
- **ONNX Runtime** (optimized inference)
- **Whisper** (speech-to-text)
- **OpenCV** (computer vision)

---

## Development Guidelines

### Coding Standards

1. **TypeScript-first**: Strong typing everywhere
2. **Small functions**: <50 lines, single responsibility
3. **Error handling**: Catch and report gracefully
4. **Comments**: Explain why, not what

### Architecture Rules

1. **Modular design**: Separate concerns clearly
2. **Local first**: Process on-device by default
3. **Lightweight defaults**: Optimize for mid-range hardware

### Testing

```bash
# Unit tests
npm test

# Integration tests
npm run test:integration

# Type checking
npm run typecheck

# Linting
npm run lint
```

---

## Getting Started

### Prerequisites

- Node.js 20+
- Rust (for Tauri)
- Python 3.10+
- FFmpeg

### Installation

```bash
# Install dependencies
npm install

# Start development
npm run dev

# Build for production
npm run build
```

---

## Roadmap

### Phase 1: Foundation ✅
- [x] Project structure
- [x] Core types and utilities
- [x] Provider manager
- [x] MCP client

### Phase 2: MCP Servers
- [ ] Video MCP server
- [ ] Audio MCP server
- [ ] Speech MCP server

### Phase 3: AI Agents
- [ ] Director agent
- [ ] Editor agent
- [ ] Subtitle agent

### Phase 4: Editor Integrations
- [ ] Premiere Pro adapter
- [ ] Clipchamp adapter
- [ ] OpenShot adapter

### Phase 5: UI/UX
- [ ] Desktop application shell
- [ ] Timeline component
- [ ] AI command bar
- [ ] Media library

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Follow coding standards
4. Write tests
5. Submit a pull request

See `docs/BUILD_BIBLE.md` for detailed guidelines.

---

## License

MIT License - See LICENSE file for details.

---

**Built with ❤️ for creators everywhere**
