# VID-ED X Performance Architecture

## Target Hardware Specifications

### Minimum Requirements
- **CPU**: Intel Core i3 4th Gen / AMD Ryzen 3 (Dual Core)
- **RAM**: 4GB
- **GPU**: Integrated Intel HD Graphics
- **Storage**: HDD supported
- **OS**: Windows 10+

### Recommended
- **CPU**: AMD Ryzen 5 / Intel Core i5
- **RAM**: 8GB
- **Storage**: SSD

## Core Design Principles

1. **Performance First** - Editor must remain responsive at all times
2. **Memory First** - Keep RAM usage under 500MB idle, 1GB during editing
3. **Battery First** - Minimize CPU/GPU usage when possible
4. **AI Second** - AI never blocks editing operations

## Implementation Status

### ✅ Verified Implemented

| Component | Status | Location |
|-----------|--------|----------|
| Hardware Detection | ✅ Implemented | `packages/core/src/performance.ts` |
| Memory Budget System | ✅ Implemented | `packages/core/src/performance.ts` |
| Proxy Resolution System | ✅ Implemented | `packages/core/src/performance.ts` |
| Adaptive Playback Quality | ✅ Implemented | `packages/core/src/performance.ts` |
| Low-Memory Mode Detection | ✅ Implemented | `packages/core/src/performance.ts` |
| Worker Pool | ✅ Implemented | `packages/core/src/performance.ts` |
| Performance Monitor | ✅ Implemented | `packages/core/src/performance.ts` |
| Job Queue System | ✅ Implemented | `packages/core/src/job-queue.ts` |
| Universal Project Format | ✅ Implemented | `packages/core/src/project.ts` |
| Timeline Utilities | ✅ Implemented | `packages/core/src/timeline.ts` |
| Core Types | ✅ Implemented | `packages/core/src/types.ts` |
| MCP Client | ✅ Implemented | `packages/mcp-client/src/mcp-client.ts` |
| Provider Manager | ✅ Implemented | `packages/providers/src/provider-manager.ts` |
| Video MCP Server | ✅ Implemented | `servers/video-mcp/` |
| Audio MCP Server | ✅ Implemented | `servers/audio-mcp/` |

### ⚠️ Partially Implemented

| Component | Status | Notes |
|-----------|--------|-------|
| MCP Connection Logic | ⚠️ Stub | `packages/mcp-client/src/mcp-client.ts` - `simulateConnection()` needs real implementation |
| Tool Discovery | ⚠️ Stub | `discoverCapabilities()` placeholder exists |
| Tool Execution | ⚠️ Stub | `executeToolImpl()` needs MCP protocol implementation |
| Provider Implementations | ⚠️ Interfaces Only | Need concrete Ollama, Gemini, OpenAI implementations |
| Tauri Backend | ⚠️ Basic | Only greet command implemented in `frontend/src-tauri/src/lib.rs` |
| Database Schema | ❌ Missing | SQLite schema not created |
| Timeline Package | ❌ Empty | `packages/timeline/src/` is empty |

### ❌ Not Implemented

| Component | Priority | Notes |
|-----------|----------|-------|
| Filesystem MCP Server | Critical | Required for secure file access |
| Timeline MCP Server | Critical | Required for timeline operations |
| Export MCP Server | Critical | Required for rendering |
| Speech MCP Server | High | Whisper integration needed |
| Subtitle MCP Server | High | Caption generation |
| Vision MCP Server | Medium | Image analysis |
| Effects MCP Server | Medium | Video effects |
| Plugin MCP Server | Medium | Plugin sandboxing |
| Provider MCP Server | Medium | AI provider tools |
| Proxy Generation Workers | Critical | Background proxy creation |
| Thumbnail Generation | Critical | Lazy thumbnail creation |
| Waveform Generation | High | Audio visualization |
| Virtual Timeline Rendering | Critical | React virtualization |
| GPU Acceleration Detection | High | NVENC/AMF/QSV detection |
| Crash Recovery | High | Autosave system |
| Editor Adapters | Medium | Premiere/Clipchamp/OpenShot export |

## Performance Optimizations Implemented

### 1. Hardware-Aware Configuration

```typescript
// Auto-detects hardware capabilities
const hardware = await detectHardware();
// Returns: cpuCores, ramGB, gpuAvailable, performanceTier

// Automatically configures memory budgets
const budget = getMemoryBudget(hardware);
// Low-end: 500MB max, 50MB thumbnail cache
// Mid-range: 1000MB max, 150MB thumbnail cache
// High-end: 2000MB max, 300MB thumbnail cache
```

### 2. Adaptive Proxy System

```typescript
// Automatically selects optimal proxy resolution
const proxyRes = getOptimalProxyResolution(hardware);
// Low-end: 360p
// Mid-range: 540p
// High-end: 720p
```

### 3. Background Job Queue

```typescript
// All heavy operations run in background
const jobQueue = getJobQueue({ maxConcurrentJobs: 2 });

// Register handlers for different job types
jobQueue.registerHandler(JobType.PROXY_GENERATION, proxyHandler);
jobQueue.registerHandler(JobType.THUMBNAIL_GENERATION, thumbnailHandler);
jobQueue.registerHandler(JobType.RENDER, renderHandler);

// Add jobs with priority scheduling
const jobId = jobQueue.addJob(
  JobType.PROXY_GENERATION,
  'Generate Proxies',
  { videoPath: '/path/to/video.mp4' },
  { priority: JobPriority.HIGH }
);
```

### 4. Worker Pool for Parallel Processing

```typescript
// Create worker pool for background tasks
const workerPool = new WorkerPool('/workers/thumbnail-worker.js', 2);

// Process tasks without blocking UI
const result = await workerPool.postTask({ type: 'generate', path: file });
```

### 5. Performance Monitoring

```typescript
// Real-time FPS and memory monitoring
const monitor = getPerformanceMonitor();
monitor.subscribe(({ fps, memoryMB }) => {
  if (fps < 24) {
    // Automatically reduce quality
    dropToLowerResolution();
  }
  if (memoryMB > 800) {
    // Aggressively unload cached assets
    clearThumbnailCache();
  }
});
```

## Memory Management Strategy

### Idle State (< 500MB)
- Thumbnail cache: 50MB
- Waveform cache: 30MB
- Proxy cache: 200MB
- Undo history: 20 items
- Preloaded clips: 3

### Editing State (< 1GB)
- Thumbnail cache: 150MB
- Waveform cache: 80MB
- Proxy cache: 500MB
- Undo history: 50 items
- Preloaded clips: 5

### Aggressive Unloading (Low Memory Mode)
When RAM ≤ 4GB:
- Disable shadows and blur effects
- Reduce animations
- Small thumbnail cache
- Aggressive asset unloading
- Limit undo history to 20 items

## Playback Engine Design

### Adaptive Quality Steps
```
1080p → 720p → 540p → 360p → 240p
```

### Automatic Degradation Triggers
- FPS drops below 24 for 3 seconds → Lower resolution
- Memory usage exceeds 80% → Clear caches
- CPU usage exceeds 90% → Skip frames

## TODO: Critical Path Items

### Phase 1: Core Stability (Weeks 1-2)
1. [ ] Implement real MCP connection logic (stdio/HTTP)
2. [ ] Build Filesystem MCP Server with security guards
3. [ ] Build Timeline MCP Server for centralized state
4. [ ] Connect Ollama API for real AI planning
5. [ ] Implement job handlers for proxy generation

### Phase 2: Data Layer (Weeks 3-4)
1. [ ] Create SQLite database schema
2. [ ] Implement thumbnail caching system
3. [ ] Implement waveform generation and caching
4. [ ] Build metadata extraction workers
5. [ ] Implement virtual timeline rendering

### Phase 3: AI Integration (Weeks 5-6)
1. [ ] Implement Ollama provider with streaming
2. [ ] Implement Gemini provider (chat only)
3. [ ] Implement OpenAI provider (chat only)
4. [ ] Build capability-based provider UI
5. [ ] Add fallback logic in ProviderManager

### Phase 4: Export & Interchange (Weeks 7-8)
1. [ ] Build Export MCP Server
2. [ ] Implement FCPXML exporter for Premiere/Clipchamp
3. [ ] Implement OpenShot JSON exporter
4. [ ] Build background render queue
5. [ ] Add crash recovery system

## Security Considerations

### Current Gaps
1. **Path Traversal**: Filesystem MCP needs path validation
2. **Prompt Injection**: AI planner accepts raw user input
3. **API Key Storage**: Currently plain text in config
4. **Plugin Sandboxing**: No isolation mechanism yet

### Required Implementations
```typescript
// Path validation example
function sanitizePath(inputPath: string): string {
  const resolved = path.resolve(inputPath);
  const allowedRoot = config.scratchDiskPath;
  
  if (!resolved.startsWith(allowedRoot)) {
    throw new Error('Path traversal detected');
  }
  
  return resolved;
}
```

## Performance Testing Checklist

- [ ] Launch time < 3 seconds on target hardware
- [ ] Timeline scrubbing at 24+ FPS with 100 clips
- [ ] Memory stays under 500MB with no project open
- [ ] Memory stays under 1GB with 4K project
- [ ] Proxy generation doesn't block UI
- [ ] Export runs in background
- [ ] AI requests don't freeze editor
- [ ] Graceful degradation on low RAM

## Conclusion

The foundation for a performance-first video editor is in place with:
- Hardware detection and adaptive configuration
- Background job queue system
- Memory budget management
- Worker pool architecture
- Performance monitoring

However, critical gaps remain in:
- Actual MCP server implementations
- Database persistence layer
- Virtual timeline rendering
- Real AI provider connections
- Security hardening

**Production Readiness**: Prototype phase. Focus on Phase 1 items before any user testing.
