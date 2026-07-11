/**
 * Video MCP Server - Main Entry Point
 * 
 * Implements the Model Context Protocol server for video processing.
 * Exposes FFmpeg-based tools through the MCP interface.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool
} from '@modelcontextprotocol/sdk/types.js';
import { VIDEO_TOOLS, ToolSchemas } from './tools';
import { VideoTools } from './ffmpeg-impl';

/** Convert Zod schema to JSON Schema for MCP */
function zodToJsonSchema(zodSchema: any): any {
  // Basic Zod to JSON Schema conversion
  // In production, use @zod-to-json-schema package
  const shape = zodSchema.shape;
  const properties: Record<string, any> = {};
  const required: string[] = [];

  for (const [key, value] of Object.entries(shape)) {
    const prop = value as any;
    properties[key] = {
      type: prop._def.typeName === 'ZodString' ? 'string' :
            prop._def.typeName === 'ZodNumber' ? 'number' :
            prop._def.typeName === 'ZodBoolean' ? 'boolean' :
            prop._def.typeName === 'ZodArray' ? 'array' :
            prop._def.typeName === 'ZodEnum' ? 'string' :
            prop._def.typeName === 'ZodOptional' ? zodToJsonSchema(prop._def.innerType) : 'any',
      description: prop.description
    };

    if (prop._def.typeName !== 'ZodOptional') {
      required.push(key);
    }
  }

  return {
    type: 'object',
    properties,
    required
  };
}

/** Create MCP Server instance */
const server = new Server(
  {
    name: 'video-mcp',
    version: '0.1.0'
  },
  {
    capabilities: {
      tools: {}
    }
  }
);

/** Register tool list handler */
server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools: Tool[] = VIDEO_TOOLS.map(tool => ({
    name: tool.name,
    description: tool.description,
    inputSchema: zodToJsonSchema(tool.inputSchema)
  }));

  return { tools };
});

/** Register tool call handler */
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    let result;

    switch (name) {
      case 'trim_video': {
        const validated = ToolSchemas.trimVideo.parse(args);
        const output = await VideoTools.trimVideo(validated);
        result = { success: true, data: output };
        break;
      }

      case 'concatenate_videos': {
        const validated = ToolSchemas.concatenateVideos.parse(args);
        const output = await VideoTools.concatenateVideos(validated);
        result = { success: true, data: output };
        break;
      }

      case 'extract_audio': {
        const validated = ToolSchemas.extractAudio.parse(args);
        const output = await VideoTools.extractAudio(validated);
        result = { success: true, data: output };
        break;
      }

      case 'get_media_info': {
        const validated = ToolSchemas.getMediaInfo.parse(args);
        const output = await VideoTools.getMediaInfo(validated);
        result = { success: true, data: output };
        break;
      }

      case 'generate_thumbnail': {
        const validated = ToolSchemas.generateThumbnail.parse(args);
        const output = await VideoTools.generateThumbnail(validated);
        result = { success: true, data: output };
        break;
      }

      case 'change_speed': {
        const validated = ToolSchemas.changeSpeed.parse(args);
        const output = await VideoTools.changeSpeed(validated);
        result = { success: true, data: output };
        break;
      }

      case 'reverse_video': {
        const validated = ToolSchemas.reverseVideo.parse(args);
        const output = await VideoTools.reverseVideo(validated);
        result = { success: true, data: output };
        break;
      }

      case 'scale_video': {
        const validated = ToolSchemas.scaleVideo.parse(args);
        const output = await VideoTools.scaleVideo(validated);
        result = { success: true, data: output };
        break;
      }

      case 'convert_format': {
        const validated = ToolSchemas.convertFormat.parse(args);
        const output = await VideoTools.convertFormat(validated);
        result = { success: true, data: output };
        break;
      }

      case 'create_color_bars': {
        const validated = ToolSchemas.createColorBars.parse(args);
        const output = await VideoTools.createColorBars(validated);
        result = { success: true, data: output };
        break;
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    
    // Validation error handling
    if (error instanceof Error && error.name === 'ZodError') {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: 'Validation error',
              details: JSON.parse(errorMessage)
            }, null, 2)
          }
        ],
        isError: true
      };
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: errorMessage
          }, null, 2)
        }
      ],
      isError: true
    };
  }
});

/** Start the server */
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error('Video MCP Server running on stdio');
  console.error('Available tools:', VIDEO_TOOLS.map(t => t.name).join(', '));
}

main().catch((error) => {
  console.error('Fatal error starting server:', error);
  process.exit(1);
});

export default server;
