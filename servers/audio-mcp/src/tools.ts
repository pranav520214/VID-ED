/**
 * Audio MCP Server - Tool Definitions
 * 
 * Defines tools for audio processing operations.
 * All tools are backed by FFmpeg implementations.
 */

import { z } from 'zod';

/** Tool input schemas using Zod for validation */
export const ToolSchemas = {
  /** Normalize audio levels */
  normalizeAudio: z.object({
    inputPath: z.string().describe('Path to input audio/video file'),
    outputPath: z.string().describe('Path for output file'),
    targetLevel: z.number().min(-50).max(0).default(-23).describe('Target loudness in LUFS')
  }),

  /** Remove silence from audio */
  removeSilence: z.object({
    inputPath: z.string().describe('Path to input audio/video file'),
    outputPath: z.string().describe('Path for output file'),
    threshold: z.number().min(0).default(0.01).describe('Silence threshold (0-1)'),
    minDuration: z.number().min(0).default(0.5).describe('Minimum silence duration to remove (seconds)')
  }),

  /** Apply fade in/out effect */
  applyFade: z.object({
    inputPath: z.string().describe('Path to input audio/video file'),
    outputPath: z.string().describe('Path for output file'),
    fadeIn: z.number().min(0).optional().default(0).describe('Fade in duration (seconds)'),
    fadeOut: z.number().min(0).optional().default(0).describe('Fade out duration (seconds)')
  }),

  /** Change audio volume */
  changeVolume: z.object({
    inputPath: z.string().describe('Path to input audio/video file'),
    outputPath: z.string().describe('Path for output file'),
    gain: z.number().min(-100).max(100).describe('Volume gain in dB')
  }),

  /** Convert audio format */
  convertAudioFormat: z.object({
    inputPath: z.string().describe('Path to input audio file'),
    outputPath: z.string().describe('Path for output audio file'),
    codec: z.enum(['aac', 'mp3', 'wav', 'flac', 'opus', 'ogg']),
    bitrate: z.number().min(8).max(320).optional().describe('Bitrate in kbps (for lossy codecs)'),
    sampleRate: z.number().optional().describe('Sample rate in Hz (e.g., 44100, 48000)')
  }),

  /** Mix multiple audio files */
  mixAudio: z.object({
    inputPaths: z.array(z.string()).min(2).describe('Array of input audio paths'),
    outputPath: z.string().describe('Path for mixed output'),
    volumes: z.array(z.number()).optional().describe('Volume for each input (0-1, default 1.0)')
  }),

  /** Extract audio spectrum data */
  analyzeSpectrum: z.object({
    inputPath: z.string().describe('Path to input audio file'),
    outputPath: z.string().optional().describe('Optional path for spectrum image output')
  }),

  /** Apply noise reduction */
  reduceNoise: z.object({
    inputPath: z.string().describe('Path to input audio file'),
    outputPath: z.string().describe('Path for output file'),
    noiseProfile: z.string().optional().describe('Optional path to noise profile sample'),
    reductionAmount: z.number().min(0).max(1).default(0.5).describe('Noise reduction amount (0-1)')
  }),

  /** Change audio pitch */
  changePitch: z.object({
    inputPath: z.string().describe('Path to input audio file'),
    outputPath: z.string().describe('Path for output file'),
    semitones: z.number().min(-24).max(24).describe('Pitch shift in semitones')
  }),

  /** Convert stereo to mono or vice versa */
  convertChannels: z.object({
    inputPath: z.string().describe('Path to input audio file'),
    outputPath: z.string().describe('Path for output file'),
    channels: z.enum(['mono', 'stereo']).describe('Target channel configuration')
  })
};

/** Tool metadata */
export interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: ReturnType<typeof z.ZodType.prototype.describe>;
}

/** List of all available audio tools */
export const AUDIO_TOOLS: ToolDefinition[] = [
  {
    name: 'normalize_audio',
    description: 'Normalize audio to target loudness level (LUFS)',
    inputSchema: ToolSchemas.normalizeAudio
  },
  {
    name: 'remove_silence',
    description: 'Detect and remove silent sections from audio',
    inputSchema: ToolSchemas.removeSilence
  },
  {
    name: 'apply_fade',
    description: 'Apply fade in and/or fade out effect',
    inputSchema: ToolSchemas.applyFade
  },
  {
    name: 'change_volume',
    description: 'Adjust audio volume/gain',
    inputSchema: ToolSchemas.changeVolume
  },
  {
    name: 'convert_audio_format',
    description: 'Convert audio to different codec/format',
    inputSchema: ToolSchemas.convertAudioFormat
  },
  {
    name: 'mix_audio',
    description: 'Mix multiple audio tracks together',
    inputSchema: ToolSchemas.mixAudio
  },
  {
    name: 'analyze_spectrum',
    description: 'Analyze audio frequency spectrum',
    inputSchema: ToolSchemas.analyzeSpectrum
  },
  {
    name: 'reduce_noise',
    description: 'Reduce background noise in audio',
    inputSchema: ToolSchemas.reduceNoise
  },
  {
    name: 'change_pitch',
    description: 'Shift audio pitch without changing speed',
    inputSchema: ToolSchemas.changePitch
  },
  {
    name: 'convert_channels',
    description: 'Convert between mono and stereo',
    inputSchema: ToolSchemas.convertChannels
  }
];

// Export type inference helpers
export type NormalizeAudioInput = z.infer<typeof ToolSchemas.normalizeAudio>;
export type RemoveSilenceInput = z.infer<typeof ToolSchemas.removeSilence>;
export type ApplyFadeInput = z.infer<typeof ToolSchemas.applyFade>;
export type ChangeVolumeInput = z.infer<typeof ToolSchemas.changeVolume>;
export type ConvertAudioFormatInput = z.infer<typeof ToolSchemas.convertAudioFormat>;
export type MixAudioInput = z.infer<typeof ToolSchemas.mixAudio>;
export type AnalyzeSpectrumInput = z.infer<typeof ToolSchemas.analyzeSpectrum>;
export type ReduceNoiseInput = z.infer<typeof ToolSchemas.reduceNoise>;
export type ChangePitchInput = z.infer<typeof ToolSchemas.changePitch>;
export type ConvertChannelsInput = z.infer<typeof ToolSchemas.convertChannels>;
