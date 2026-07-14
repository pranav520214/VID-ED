"""
AI Director Agent

The AI Director uses Gemma (via Ollama) to understand natural language requests
and generate structured edit plans that are executed by MCP servers.

Gemma is the DIRECTOR, not the editor. It plans; MCP servers execute.
"""

import json
import uuid
from typing import Any, Optional

import httpx
from loguru import logger

from packages.mcp_client.protocol import EditPlan, MCPServerType, TaskNode


class AIDirector:
    """
    AI Director Agent powered by Gemma via Ollama.
    
    The Director:
    1. Receives natural language editing requests
    2. Analyzes the request and available MCP tools
    3. Creates a structured task graph (EditPlan)
    4. Returns the plan for execution by the MCP Client
    
    NEVER generates FFmpeg commands directly - always uses MCP tools.
    """

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        model: str = "gemma3:4b-instruct",
    ):
        self.ollama_base_url = ollama_base_url
        self.model = model
        self.available_tools: list[dict[str, Any]] = []

    def set_available_tools(self, tools: list[dict[str, Any]]) -> None:
        """Set the list of available MCP tools."""
        self.available_tools = tools
        logger.info(f"AI Director loaded {len(tools)} available tools")

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the AI Director."""
        tools_json = json.dumps(self.available_tools, indent=2)
        
        return f"""You are the AI Director for VID-ED AI, a professional video editing application.

YOUR ROLE: You are the DIRECTOR, not the editor. You create editing plans that are executed by MCP servers.

IMPORTANT RULES:
1. NEVER output FFmpeg commands or code
2. ALWAYS use the available MCP tools listed below
3. Create a structured task graph with proper dependencies
4. Each task must specify which MCP server type handles it
5. Consider task dependencies (e.g., detect silence BEFORE removing it)

AVAILABLE MCP TOOLS:
{tools_json}

OUTPUT FORMAT:
You must output a JSON object with this exact structure:
{{
    "plan_id": "unique-id-here",
    "tasks": [
        {{
            "id": "task-1",
            "tool_name": "remove_silence",
            "server_type": "speech",
            "parameters": {{"audio_path": "/path/to/audio.mp3"}},
            "dependencies": []
        }},
        {{
            "id": "task-2", 
            "tool_name": "cut",
            "server_type": "video",
            "parameters": {{"clip_id": "main", "start_time": 0, "end_time": 10}},
            "dependencies": ["task-1"]
        }}
    ]
}}

SERVER TYPES AVAILABLE:
- video: Video manipulation (trim, cut, merge, crop, zoom, etc.)
- audio: Audio processing (noise removal, normalize, compress, etc.)
- speech: Speech processing (transcription, subtitles, silence detection)
- vision: Computer vision (object detection, face tracking, scene detection)
- subtitle: Subtitle generation and styling
- effects: Visual effects (transitions, blur, glow, etc.)
- color: Color grading (white balance, LUT, exposure, etc.)
- export: Export presets for different platforms
- render: Final rendering

Think step-by-step about what the user wants, then create a logical sequence of tasks."""

    async def generate_plan(self, user_request: str, context: Optional[dict] = None) -> EditPlan:
        """
        Generate an edit plan from a natural language request.
        
        Args:
            user_request: Natural language description of desired edits
            context: Optional context about the project (media paths, etc.)
            
        Returns:
            EditPlan object with structured tasks
        """
        if not self.available_tools:
            raise ValueError("No MCP tools registered. Call set_available_tools() first.")
        
        context_str = json.dumps(context) if context else "No additional context provided."
        
        prompt = f"""
CONTEXT ABOUT PROJECT:
{context_str}

USER REQUEST:
{user_request}

Generate the edit plan as JSON:
"""
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "system": self._build_system_prompt(),
                        "stream": False,
                        "format": "json",
                    },
                )
                response.raise_for_status()
                result = response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"Ollama API error: {e}")
            # Fallback: create a simple plan
            return self._create_fallback_plan(user_request)
        except Exception as e:
            logger.error(f"Failed to generate plan: {e}")
            return self._create_fallback_plan(user_request)
        
        # Parse the response
        try:
            response_text = result.get("response", "")
            plan_data = json.loads(response_text)
            return self._parse_plan_data(plan_data, user_request)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return self._create_fallback_plan(user_request)

    def _parse_plan_data(self, plan_data: dict, user_request: str) -> EditPlan:
        """Parse raw plan data into EditPlan object."""
        plan_id = plan_data.get("plan_id", str(uuid.uuid4()))
        tasks_data = plan_data.get("tasks", [])
        
        tasks = []
        for task_data in tasks_data:
            try:
                server_type = MCPServerType(task_data.get("server_type", "video"))
                task = TaskNode(
                    id=task_data.get("id", str(uuid.uuid4())),
                    tool_name=task_data.get("tool_name", ""),
                    server_type=server_type,
                    parameters=task_data.get("parameters", {}),
                    dependencies=task_data.get("dependencies", []),
                )
                tasks.append(task)
            except ValueError as e:
                logger.warning(f"Invalid server type in task: {e}")
                continue
        
        return EditPlan(
            plan_id=plan_id,
            user_request=user_request,
            tasks=tasks,
            metadata=plan_data.get("metadata", {}),
        )

    def _create_fallback_plan(self, user_request: str) -> EditPlan:
        """Create a basic fallback plan when AI fails."""
        logger.warning("Creating fallback plan for request")
        
        # Simple keyword-based plan generation
        request_lower = user_request.lower()
        tasks = []
        
        if "subtitle" in request_lower or "caption" in request_lower:
            tasks.append(TaskNode(
                id="task-1",
                tool_name="subtitle_generation",
                server_type=MCPServerType.SPEECH,
                parameters={"audio_path": "${project_audio}"},
                dependencies=[],
            ))
        
        if "silence" in request_lower and ("remove" in request_lower or "cut" in request_lower):
            tasks.append(TaskNode(
                id="task-2",
                tool_name="remove_silence",
                server_type=MCPServerType.SPEECH,
                parameters={"audio_path": "${project_audio}"},
                dependencies=[],
            ))
        
        if "noise" in request_lower and ("remove" in request_lower or "clean" in request_lower):
            tasks.append(TaskNode(
                id="task-3",
                tool_name="noise_removal",
                server_type=MCPServerType.AUDIO,
                parameters={"audio_path": "${project_audio}"},
                dependencies=[],
            ))
        
        if "export" in request_lower or "render" in request_lower:
            tasks.append(TaskNode(
                id="task-4",
                tool_name="render",
                server_type=MCPServerType.VIDEO,
                parameters={"clip_id": "main", "output_path": "${project_export}"},
                dependencies=[t.id for t in tasks],
            ))
        
        return EditPlan(
            plan_id=str(uuid.uuid4()),
            user_request=user_request,
            tasks=tasks,
            metadata={"fallback": True},
        )

    async def explain_plan(self, plan: EditPlan) -> str:
        """Generate a human-readable explanation of the plan."""
        explanation = f"**Edit Plan: {plan.plan_id}**\n\n"
        explanation += f"**Request:** {plan.user_request}\n\n"
        explanation += "**Steps:**\n\n"
        
        for i, task in enumerate(plan.tasks, 1):
            deps = f" (after: {', '.join(task.dependencies)})" if task.dependencies else ""
            explanation += f"{i}. **{task.tool_name}** ({task.server_type.value}){deps}\n"
            if task.parameters:
                params = ", ".join(f"{k}={v}" for k, v in task.parameters.items())
                explanation += f"   - Parameters: {params}\n"
        
        return explanation
