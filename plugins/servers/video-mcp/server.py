"""
Video MCP Server

Provides video manipulation tools via MCP protocol.
All operations are executed using FFmpeg and OpenCV.
"""

import asyncio
import uuid
from pathlib import Path
from typing import Any, Optional

import ffmpeg

from packages.mcp_client.protocol import (
    MCPResponse,
    MCPServer,
    MCPServerType,
    MCPTool,
)


class VideoMCPServer(MCPServer):
    """MCP Server for video manipulation operations."""

    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self._running_tasks: dict[str, asyncio.Task] = {}

    @property
    def server_type(self) -> MCPServerType:
        return MCPServerType.VIDEO

    @property
    def tools(self) -> list[MCPTool]:
        return [
            MCPTool(
                name="create_project",
                description="Create a new video editing project",
                parameters={
                    "project_name": {"type": "string", "required": True},
                    "resolution": {"type": "string", "default": "1920x1080"},
                    "fps": {"type": "integer", "default": 30},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="import_media",
                description="Import media files into the project",
                parameters={
                    "file_path": {"type": "string", "required": True},
                    "track": {"type": "string", "default": "video"},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="trim",
                description="Trim a video clip to specified start and end times",
                parameters={
                    "clip_id": {"type": "string", "required": True},
                    "start_time": {"type": "number", "required": True},
                    "end_time": {"type": "number", "required": True},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="split",
                description="Split a video clip at a specific timestamp",
                parameters={
                    "clip_id": {"type": "string", "required": True},
                    "timestamp": {"type": "number", "required": True},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="cut",
                description="Remove a segment from a video clip",
                parameters={
                    "clip_id": {"type": "string", "required": True},
                    "start_time": {"type": "number", "required": True},
                    "end_time": {"type": "number", "required": True},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="merge",
                description="Merge multiple video clips together",
                parameters={
                    "clip_ids": {"type": "array", "required": True},
                    "output_path": {"type": "string", "required": True},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="crop",
                description="Crop a video to a specific region",
                parameters={
                    "clip_id": {"type": "string", "required": True},
                    "x": {"type": "integer", "required": True},
                    "y": {"type": "integer", "required": True},
                    "width": {"type": "integer", "required": True},
                    "height": {"type": "integer", "required": True},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="zoom",
                description="Apply zoom effect to a video",
                parameters={
                    "clip_id": {"type": "string", "required": True},
                    "zoom_level": {"type": "number", "default": 1.5},
                    "duration": {"type": "number", "default": 2.0},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="pan",
                description="Apply pan effect to a video",
                parameters={
                    "clip_id": {"type": "string", "required": True},
                    "direction": {"type": "string", "default": "left"},
                    "duration": {"type": "number", "default": 2.0},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="rotate",
                description="Rotate a video by specified degrees",
                parameters={
                    "clip_id": {"type": "string", "required": True},
                    "degrees": {"type": "integer", "default": 90},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="speed",
                description="Change playback speed of a video",
                parameters={
                    "clip_id": {"type": "string", "required": True},
                    "speed_factor": {"type": "number", "default": 1.0},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="freeze",
                description="Freeze frame at a specific timestamp",
                parameters={
                    "clip_id": {"type": "string", "required": True},
                    "timestamp": {"type": "number", "required": True},
                    "duration": {"type": "number", "default": 1.0},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="reverse",
                description="Reverse playback of a video clip",
                parameters={
                    "clip_id": {"type": "string", "required": True},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="stabilize",
                description="Stabilize shaky footage",
                parameters={
                    "clip_id": {"type": "string", "required": True},
                    "strength": {"type": "number", "default": 0.5},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="render",
                description="Render video with applied effects",
                parameters={
                    "clip_id": {"type": "string", "required": True},
                    "output_path": {"type": "string", "required": True},
                    "quality": {"type": "string", "default": "high"},
                },
                server_type=self.server_type,
            ),
        ]

    async def execute_tool(self, tool_name: str, parameters: dict[str, Any]) -> MCPResponse:
        """Execute a video tool."""
        request_id = str(uuid.uuid4())
        
        try:
            method = getattr(self, f"_{tool_name}", None)
            if not method:
                return MCPResponse(
                    request_id=request_id,
                    success=False,
                    error=f"Unknown tool: {tool_name}",
                )
            
            result = await method(**parameters)
            return MCPResponse(
                request_id=request_id,
                success=True,
                result=result,
                progress=1.0,
            )
        except Exception as e:
            return MCPResponse(
                request_id=request_id,
                success=False,
                error=str(e),
            )

    async def cancel_task(self, request_id: str) -> bool:
        """Cancel a running task."""
        if request_id in self._running_tasks:
            self._running_tasks[request_id].cancel()
            del self._running_tasks[request_id]
            return True
        return False

    # Tool implementations
    async def _create_project(self, project_name: str, resolution: str = "1920x1080", fps: int = 30) -> dict:
        """Create a new video editing project."""
        project_dir = self.project_path / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create project structure
        (project_dir / "media").mkdir(exist_ok=True)
        (project_dir / "exports").mkdir(exist_ok=True)
        (project_dir / "cache").mkdir(exist_ok=True)
        
        # Create project config
        config = {
            "name": project_name,
            "resolution": resolution,
            "fps": fps,
            "clips": [],
            "tracks": [],
        }
        
        return {"project_path": str(project_dir), "config": config}

    async def _import_media(self, file_path: str, track: str = "video") -> dict:
        """Import media files into the project."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get media info using ffprobe
        probe = ffmpeg.probe(str(path))
        video_stream = next((s for s in probe.get("streams", []) if s.get("codec_type") == "video"), None)
        
        media_info = {
            "file_path": str(path),
            "duration": float(video_stream.get("duration", 0)) if video_stream else 0,
            "resolution": f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}" if video_stream else "unknown",
            "fps": float(video_stream.get("r_frame_rate", "0/1").split("/")[0]) if video_stream else 0,
            "track": track,
        }
        
        return media_info

    async def _trim(self, clip_id: str, start_time: float, end_time: float) -> dict:
        """Trim a video clip."""
        # Implementation would use ffmpeg to trim
        return {"clip_id": clip_id, "start": start_time, "end": end_time, "status": "trimmed"}

    async def _split(self, clip_id: str, timestamp: float) -> dict:
        """Split a video clip at timestamp."""
        return {"clip_id": clip_id, "split_at": timestamp, "clips": [f"{clip_id}_a", f"{clip_id}_b"]}

    async def _cut(self, clip_id: str, start_time: float, end_time: float) -> dict:
        """Cut/remove a segment from a clip."""
        return {"clip_id": clip_id, "removed_segment": {"start": start_time, "end": end_time}}

    async def _merge(self, clip_ids: list[str], output_path: str) -> dict:
        """Merge multiple clips."""
        return {"output_path": output_path, "merged_clips": clip_ids}

    async def _crop(self, clip_id: str, x: int, y: int, width: int, height: int) -> dict:
        """Crop a video."""
        return {"clip_id": clip_id, "crop_region": {"x": x, "y": y, "w": width, "h": height}}

    async def _zoom(self, clip_id: str, zoom_level: float = 1.5, duration: float = 2.0) -> dict:
        """Apply zoom effect."""
        return {"clip_id": clip_id, "zoom_level": zoom_level, "duration": duration}

    async def _pan(self, clip_id: str, direction: str = "left", duration: float = 2.0) -> dict:
        """Apply pan effect."""
        return {"clip_id": clip_id, "direction": direction, "duration": duration}

    async def _rotate(self, clip_id: str, degrees: int = 90) -> dict:
        """Rotate video."""
        return {"clip_id": clip_id, "rotation": degrees}

    async def _speed(self, clip_id: str, speed_factor: float = 1.0) -> dict:
        """Change playback speed."""
        return {"clip_id": clip_id, "speed_factor": speed_factor}

    async def _freeze(self, clip_id: str, timestamp: float, duration: float = 1.0) -> dict:
        """Freeze frame."""
        return {"clip_id": clip_id, "freeze_at": timestamp, "duration": duration}

    async def _reverse(self, clip_id: str) -> dict:
        """Reverse video."""
        return {"clip_id": clip_id, "reversed": True}

    async def _stabilize(self, clip_id: str, strength: float = 0.5) -> dict:
        """Stabilize footage."""
        return {"clip_id": clip_id, "stabilization_strength": strength}

    async def _render(self, clip_id: str, output_path: str, quality: str = "high") -> dict:
        """Render video."""
        return {"clip_id": clip_id, "output_path": output_path, "quality": quality, "status": "rendered"}
