/**
 * Video MCP Server - Tool Definitions
 * 
 * This module defines the tools exposed by the Video MCP server.
 * All tools are backed by FFmpeg implementations.
 */

import { z } from 'zod';

/** Tool input schemas using Zod for validation */
export const ToolSchemas = {
  /** Trim a video file to specified in/out points */
  trimVideo: z.object({
    inputPath: z.string().describe('Path to input video file'),
    outputPath: z.string().describe('Path for output video file'),
    inPoint: z.number().min(0).describe('Start time in seconds'),
    outPoint: z.number().min(0).describe('End time in seconds'),
    codec: z.enum(['h264', 'h265', 'prores', 'copy']).optional().default('copy')
  }),

  /** Concatenate multiple video files */
  concatenateVideos: z.object({
    inputPaths: z.array(z.string()).min(2).describe('Array of input video paths'),
    outputPath: z.string().describe('Path for output concatenated video'),
    codec: z.enum(['h264', 'h265', 'prores', 'copy']).optional().default('copy')
  }),

  /** Extract audio from video */
  extractAudio: z.object({
    inputPath: z.string().describe('Path to input video file'),
    outputPath: z.string().describe('Path for output audio file'),
    audioCodec: z.enum(['aac', 'mp3', 'wav', 'flac', 'copy']).optional().default('copy')
  }),

  /** Get media information using ffprobe */
  getMediaInfo: z.object({
    inputPath: z.string().describe('Path to media file')
  }),

  /** Generate thumbnail from video */
  generateThumbnail: z.object({
    inputPath: z.string().describe('Path to input video file'),
    outputPath: z.string().describe('Path for output thumbnail image'),
    timePosition: z.number().min(0).describe('Time position in seconds'),
    width: z.number().min(1).max(3840).optional().default(1920),
    height: z.number().min(1).max(2160).optional().default(1080)
  }),

  /** Change video speed */
  changeSpeed: z.object({
    inputPath: z.string().describe('Path to input video file'),
    outputPath: z.string().describe('Path for output video file'),
    speedMultiplier: z.number().min(0.1).max(10).describe('Speed multiplier (0.5 = half speed, 2 = double speed)'),
    audioPitch: z.boolean().optional().default(true).describe('Whether to preserve audio pitch')
  }),

  /** Reverse video playback */
  reverseVideo: z.object({
    inputPath: z.string().describe('Path to input video file'),
    outputPath: z.string().describe('Path for output reversed video')
  }),

  /** Scale/resize video */
  scaleVideo: z.object({
    inputPath: z.string().describe('Path to input video file'),
    outputPath: z.string().describe('Path for output video file'),
    width: z.number().min(1).optional(),
    height: z.number().min(1).optional(),
    maintainAspectRatio: z.boolean().optional().default(true),
    codec: z.enum(['h264', 'h265', 'prores']).optional().default('h264')
  }),

  /** Convert video format/codec */
  convertFormat: z.object({
    inputPath: z.string().describe('Path to input video file'),
    outputPath: z.string().describe('Path for output video file'),
    container: z.enum(['mp4', 'mov', 'mkv', 'avi', 'webm']).describe('Output container format'),
    videoCodec: z.enum(['h264', 'h265', 'av1', 'vp9', 'prores']).optional(),
    audioCodec: z.enum(['aac', 'mp3', 'wav', 'flac', 'opus']).optional(),
    bitrate: z.number().min(100).optional().describe('Bitrate in kbps'),
    crf: z.number().min(0).max(51).optional().describe('Constant Rate Factor for quality (0-51, lower is better)')
  }),

  /** Create color bar test pattern */
  createColorBars: z.object({
    outputPath: z.string().describe('Path for output video file'),
    duration: z.number().min(1).describe('Duration in seconds'),
    width: z.number().min(1).optional().default(1920),
    height: z.number().min(1).optional().default(1080),
    frameRate: z.number().min(1).optional().default(30)
  })
};

/** Tool metadata */
export interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: ReturnType<typeof z.ZodType.prototype.describe>;
}

/** List of all available video tools */
export const VIDEO_TOOLS: ToolDefinition[] = [
  {
    name: 'trim_video',
    description: 'Trim a video file to specified in/out points without re-encoding when possible',
    inputSchema: ToolSchemas.trimVideo
  },
  {
    name: 'concatenate_videos',
    description: 'Concatenate multiple video files into a single video',
    inputSchema: ToolSchemas.concatenateVideos
  },
  {
    name: 'extract_audio',
    description: 'Extract audio track from a video file',
    inputSchema: ToolSchemas.extractAudio
  },
  {
    name: 'get_media_info',
    description: 'Get detailed media information including duration, codecs, resolution, and frame rate',
    inputSchema: ToolSchemas.getMediaInfo
  },
  {
    name: 'generate_thumbnail',
    description: 'Generate a thumbnail image from a specific time position in a video',
    inputSchema: ToolSchemas.generateThumbnail
  },
  {
    name: 'change_speed',
    description: 'Change video playback speed with optional audio pitch preservation',
    inputSchema: ToolSchemas.changeSpeed
  },
  {
    name: 'reverse_video',
    description: 'Reverse video playback direction',
    inputSchema: ToolSchemas.reverseVideo
  },
  {
    name: 'scale_video',
    description: 'Scale/resize video to different dimensions',
    inputSchema: ToolSchemas.scaleVideo
  },
  {
    name: 'convert_format',
    description: 'Convert video to different format/container with codec options',
    inputSchema: ToolSchemas.convertFormat
  },
  {
    name: 'create_color_bars',
    description: 'Create a color bar test pattern video',
    inputSchema: ToolSchemas.createColorBars
  }
];

// Export individual schemas for use in implementation
export type TrimVideoInput = z.infer<typeof ToolSchemas.trimVideo>;
export type ConcatenateVideosInput = z.infer<typeof ToolSchemas.concatenateVideos>;
export type ExtractAudioInput = z.infer<typeof ToolSchemas.extractAudio>;
export type GetMediaInfoInput = z.infer<typeof ToolSchemas.getMediaInfo>;
export type GenerateThumbnailInput = z.infer<typeof ToolSchemas.generateThumbnail>;
export type ChangeSpeedInput = z.infer<typeof ToolSchemas.changeSpeed>;
export type ReverseVideoInput = z.infer<typeof ToolSchemas.reverseVideo>;
export type ScaleVideoInput = z.infer<typeof ToolSchemas.scaleVideo>;
export type ConvertFormatInput = z.infer<typeof ToolSchemas.convertFormat>;
export type CreateColorBarsInput = z.infer<typeof ToolSchemas.createColorBars>;
