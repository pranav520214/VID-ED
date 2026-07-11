# Video MCP Server

Model Context Protocol (MCP) server for video processing operations using FFmpeg.

## Overview

This MCP server provides video processing tools through the Model Context Protocol, enabling AI agents and applications to perform video operations programmatically.

## Prerequisites

- **Node.js** >= 20.0.0
- **FFmpeg** installed on the system
- **ffprobe** (included with FFmpeg)

### Installing FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update && sudo apt-get install -y ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html or use:
```bash
choco install ffmpeg
```

## Installation

```bash
npm install
npm run build
```

## Available Tools

| Tool | Description |
|------|-------------|
| `trim_video` | Trim video to specified in/out points |
| `concatenate_videos` | Join multiple videos into one |
| `extract_audio` | Extract audio track from video |
| `get_media_info` | Get detailed media metadata |
| `generate_thumbnail` | Create thumbnail image from video |
| `change_speed` | Adjust playback speed |
| `reverse_video` | Reverse video playback |
| `scale_video` | Resize video dimensions |
| `convert_format` | Convert container/codec format |
| `create_color_bars` | Generate test pattern video |

## Usage

### As MCP Server (stdio transport)

```bash
npm start
```

The server communicates via stdio using the MCP protocol.

### Example: Connecting from MCP Client

```typescript
import { MCPClient } from '@vid-ed-x/mcp-client';

const client = new MCPClient();

client.registerServer({
  id: 'video-mcp-1',
  name: 'Video MCP',
  type: MCPServerType.VIDEO,
  transport: TransportType.STDIO,
  command: 'node',
  args: ['/path/to/video-mcp/dist/index.js'],
  autoStart: true
});

await client.connectServer('video-mcp-1');

// List available tools
const tools = client.getTools('video-mcp-1');

// Execute a tool
const result = await client.executeTool(
  'video-mcp-1',
  'trim_video',
  {
    inputPath: '/path/to/input.mp4',
    outputPath: '/path/to/output.mp4',
    inPoint: 0,
    outPoint: 10
  }
);
```

## Tool Specifications

### trim_video

Trim a video file without re-encoding when possible.

**Parameters:**
- `inputPath` (string): Path to input video
- `outputPath` (string): Path for output video
- `inPoint` (number): Start time in seconds
- `outPoint` (number): End time in seconds
- `codec` (string, optional): Output codec ('copy', 'h264', 'h265', 'prores')

**Example:**
```json
{
  "inputPath": "/videos/source.mp4",
  "outputPath": "/videos/trimmed.mp4",
  "inPoint": 5.5,
  "outPoint": 15.0,
  "codec": "copy"
}
```

### get_media_info

Extract comprehensive metadata from media files.

**Parameters:**
- `inputPath` (string): Path to media file

**Returns:**
```json
{
  "duration": 120.5,
  "width": 1920,
  "height": 1080,
  "frameRate": 29.97,
  "videoCodec": "h264",
  "audioCodec": "aac",
  "fileSize": 52428800,
  "bitRate": 5000000
}
```

### generate_thumbnail

Create a thumbnail image from a specific time position.

**Parameters:**
- `inputPath` (string): Path to video
- `outputPath` (string): Path for thumbnail image
- `timePosition` (number): Time in seconds
- `width` (number, optional): Thumbnail width (default: 1920)
- `height` (number, optional): Thumbnail height (default: 1080)

## Error Handling

All tools return structured error responses:

```json
{
  "success": false,
  "error": "Error message",
  "details": {} // Optional additional details
}
```

Common errors:
- File not found
- Invalid parameters
- FFmpeg encoding errors
- Unsupported codec/format

## Testing

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- video-mcp.test.ts
```

### Test Fixtures

Place test video files in `fixtures/` directory for integration tests:
- `fixtures/test_video.mp4` - Used by integration tests

## Architecture

```
src/
├── index.ts          # MCP server entry point
├── tools.ts          # Tool definitions and Zod schemas
├── ffmpeg-impl.ts    # FFmpeg implementations
└── types.ts          # (Optional) Additional types

tests/
└── video-mcp.test.ts # Unit and integration tests
```

## Performance Considerations

1. **Stream Copy**: Use `codec: "copy"` for fast trimming without re-encoding
2. **Hardware Acceleration**: Consider enabling NVENC/QuickSync for H264/H265
3. **Memory**: Large videos may require significant RAM during processing
4. **Disk I/O**: Ensure adequate scratch disk space for temporary files

## Limitations

- `concatenate_videos` with stream copy requires special handling (see code comments)
- `reverse_video` requires two-pass encoding and can be slow
- Speed changes outside 0.5x-2.0x may affect audio quality

## Security

- Input file paths are validated for existence and readability
- Output directories are created automatically
- No shell execution - all FFmpeg calls use fluent-ffmpeg API
- Consider sandboxing for production deployments

## License

MIT
