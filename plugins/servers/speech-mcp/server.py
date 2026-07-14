"""
Speech MCP Server

Provides speech processing tools via MCP protocol.
Handles transcription, speaker detection, subtitle generation, and more.
"""

import asyncio
import uuid
from pathlib import Path
from typing import Any, Optional

from packages.mcp_client.protocol import (
    MCPResponse,
    MCPServer,
    MCPServerType,
    MCPTool,
)


class SpeechMCPServer(MCPServer):
    """MCP Server for speech processing operations."""

    def __init__(self, project_path: Optional[Path] = None, model_size: str = "tiny"):
        self.project_path = project_path or Path.cwd()
        self.model_size = model_size  # tiny, base, small, medium, large
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._whisper_model = None

    @property
    def server_type(self) -> MCPServerType:
        return MCPServerType.SPEECH

    @property
    def tools(self) -> list[MCPTool]:
        return [
            MCPTool(
                name="speech_to_text",
                description="Transcribe audio to text using Whisper",
                parameters={
                    "audio_path": {"type": "string", "required": True},
                    "language": {"type": "string", "default": "en"},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="speaker_detection",
                description="Detect different speakers in audio",
                parameters={
                    "audio_path": {"type": "string", "required": True},
                    "min_speakers": {"type": "integer", "default": 1},
                    "max_speakers": {"type": "integer", "default": 5},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="translate",
                description="Translate transcribed text to another language",
                parameters={
                    "text": {"type": "string", "required": True},
                    "source_lang": {"type": "string", "default": "en"},
                    "target_lang": {"type": "string", "required": True},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="subtitle_generation",
                description="Generate subtitles from audio with timing",
                parameters={
                    "audio_path": {"type": "string", "required": True},
                    "format": {"type": "string", "default": "srt"},
                    "language": {"type": "string", "default": "en"},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="keyword_detection",
                description="Detect specific keywords in audio",
                parameters={
                    "audio_path": {"type": "string", "required": True},
                    "keywords": {"type": "array", "required": True},
                },
                server_type=self.server_type,
            ),
            MCPTool(
                name="remove_silence",
                description="Detect and remove silent segments from audio",
                parameters={
                    "audio_path": {"type": "string", "required": True},
                    "threshold_db": {"type": "number", "default": -40},
                    "min_silence_duration": {"type": "number", "default": 0.5},
                },
                server_type=self.server_type,
            ),
        ]

    async def execute_tool(self, tool_name: str, parameters: dict[str, Any]) -> MCPResponse:
        """Execute a speech tool."""
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

    def _load_whisper_model(self):
        """Lazy load Whisper model."""
        if self._whisper_model is None:
            import whisper
            self._whisper_model = whisper.load_model(self.model_size)
        return self._whisper_model

    # Tool implementations
    async def _speech_to_text(self, audio_path: str, language: str = "en") -> dict:
        """Transcribe audio using Whisper."""
        model = self._load_whisper_model()
        result = model.transcribe(audio_path, language=language)
        
        return {
            "audio_path": audio_path,
            "text": result["text"],
            "segments": result.get("segments", []),
            "language": result.get("language", language),
        }

    async def _speaker_detection(
        self,
        audio_path: str,
        min_speakers: int = 1,
        max_speakers: int = 5,
    ) -> dict:
        """Detect speakers using pyannote or similar."""
        # Placeholder - would use pyannote.audio
        return {
            "audio_path": audio_path,
            "speakers": [],  # List of {start, end, speaker_id}
            "num_speakers": 0,
        }

    async def _translate(self, text: str, source_lang: str = "en", target_lang: str = "es") -> dict:
        """Translate text to target language."""
        # Placeholder - would use NLLB or M2M100
        return {
            "original_text": text,
            "translated_text": f"[Translated to {target_lang}] {text}",
            "source_lang": source_lang,
            "target_lang": target_lang,
        }

    async def _subtitle_generation(
        self,
        audio_path: str,
        format: str = "srt",
        language: str = "en",
    ) -> dict:
        """Generate subtitle file from audio."""
        model = self._load_whisper_model()
        result = model.transcribe(audio_path, language=language)
        
        # Generate SRT content
        srt_content = ""
        for i, segment in enumerate(result.get("segments", []), 1):
            start = self._format_srt_time(segment["start"])
            end = self._format_srt_time(segment["end"])
            text = segment["text"].strip()
            srt_content += f"{i}\n{start} --> {end}\n{text}\n\n"
        
        output_path = self.project_path / "cache" / f"subtitles.srt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(srt_content)
        
        return {
            "audio_path": audio_path,
            "format": format,
            "output_path": str(output_path),
            "segments": result.get("segments", []),
        }

    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT time format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    async def _keyword_detection(self, audio_path: str, keywords: list[str]) -> dict:
        """Detect keywords in audio."""
        # Would use keyword spotting model
        return {
            "audio_path": audio_path,
            "keywords": keywords,
            "occurrences": [],  # List of {keyword, timestamp, confidence}
        }

    async def _remove_silence(
        self,
        audio_path: str,
        threshold_db: float = -40,
        min_silence_duration: float = 0.5,
    ) -> dict:
        """Remove silent segments from audio."""
        # Would use librosa to detect silence
        return {
            "audio_path": audio_path,
            "threshold_db": threshold_db,
            "min_silence_duration": min_silence_duration,
            "silence_segments": [],  # List of {start, end}
            "output_path": str(self.project_path / "cache" / f"no_silence_{Path(audio_path).name}"),
        }
