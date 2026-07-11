/**
 * Audio MCP Server - Main Entry Point
 * 
 * Implements the Model Context Protocol server for audio processing.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool
} from '@modelcontextprotocol/sdk/types.js';
import { AUDIO_TOOLS, ToolSchemas } from './tools';
import { AudioTools } from './ffmpeg-impl';

function zodToJsonSchema(zodSchema: any): any {
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

const server = new Server(
  {
    name: 'audio-mcp',
    version: '0.1.0'
  },
  {
    capabilities: {
      tools: {}
    }
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools: Tool[] = AUDIO_TOOLS.map(tool => ({
    name: tool.name,
    description: tool.description,
    inputSchema: zodToJsonSchema(tool.inputSchema)
  }));

  return { tools };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    let result;

    switch (name) {
      case 'normalize_audio': {
        const validated = ToolSchemas.normalizeAudio.parse(args);
        const output = await AudioTools.normalizeAudio(validated);
        result = { success: true, data: output };
        break;
      }

      case 'remove_silence': {
        const validated = ToolSchemas.removeSilence.parse(args);
        const output = await AudioTools.removeSilence(validated);
        result = { success: true, data: output };
        break;
      }

      case 'apply_fade': {
        const validated = ToolSchemas.applyFade.parse(args);
        const output = await AudioTools.applyFade(validated);
        result = { success: true, data: output };
        break;
      }

      case 'change_volume': {
        const validated = ToolSchemas.changeVolume.parse(args);
        const output = await AudioTools.changeVolume(validated);
        result = { success: true, data: output };
        break;
      }

      case 'convert_audio_format': {
        const validated = ToolSchemas.convertAudioFormat.parse(args);
        const output = await AudioTools.convertAudioFormat(validated);
        result = { success: true, data: output };
        break;
      }

      case 'mix_audio': {
        const validated = ToolSchemas.mixAudio.parse(args);
        const output = await AudioTools.mixAudio(validated);
        result = { success: true, data: output };
        break;
      }

      case 'analyze_spectrum': {
        const validated = ToolSchemas.analyzeSpectrum.parse(args);
        const output = await AudioTools.analyzeSpectrum(validated);
        result = { success: true, data: output };
        break;
      }

      case 'reduce_noise': {
        const validated = ToolSchemas.reduceNoise.parse(args);
        const output = await AudioTools.reduceNoise(validated);
        result = { success: true, data: output };
        break;
      }

      case 'change_pitch': {
        const validated = ToolSchemas.changePitch.parse(args);
        const output = await AudioTools.changePitch(validated);
        result = { success: true, data: output };
        break;
      }

      case 'convert_channels': {
        const validated = ToolSchemas.convertChannels.parse(args);
        const output = await AudioTools.convertChannels(validated);
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

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error('Audio MCP Server running on stdio');
  console.error('Available tools:', AUDIO_TOOLS.map(t => t.name).join(', '));
}

main().catch((error) => {
  console.error('Fatal error starting server:', error);
  process.exit(1);
});

export default server;
