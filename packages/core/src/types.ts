/**
 * Core Type Definitions for VID-ED X
 */

/** Unique identifier type */
export type ID = string;

/** Time in seconds */
export type Time = number;

/** Time range with start and end in seconds */
export interface TimeRange {
  start: Time;
  end: Time;
}

/** Supported media types */
export enum MediaType {
  VIDEO = 'video',
  AUDIO = 'audio',
  IMAGE = 'image',
  TEXT = 'text',
  FONT = 'font'
}

/** Video codec types */
export enum VideoCodec {
  H264 = 'h264',
  H265 = 'h265',
  AV1 = 'av1',
  VP9 = 'vp9',
  PRORES = 'prores',
  RAW = 'raw'
}

/** Audio codec types */
export enum AudioCodec {
  AAC = 'aac',
  MP3 = 'mp3',
  WAV = 'wav',
  FLAC = 'flac',
  OPUS = 'opus',
  PCM = 'pcm'
}

/** Resolution presets */
export enum ResolutionPreset {
  HD_720p = '720p',
  FULL_HD_1080p = '1080p',
  QHD_2K = '2k',
  UHD_4K = '4k',
  UHD_8K = '8k'
}

/** Aspect ratio types */
export enum AspectRatio {
  LANDSCAPE_16_9 = '16:9',
  PORTRAIT_9_16 = '9:16',
  SQUARE_1_1 = '1:1',
  CINEMATIC_21_9 = '21:9',
  SOCIAL_4_5 = '4:5'
}

/** Frame rate presets */
export enum FrameRate {
  FPS_24 = 24,
  FPS_25 = 25,
  FPS_30 = 30,
  FPS_50 = 50,
  FPS_60 = 60,
  FPS_120 = 120
}

/** Export format configuration */
export interface ExportFormat {
  container: string; // mp4, mov, mkv, avi, webm
  videoCodec?: VideoCodec;
  audioCodec?: AudioCodec;
  resolution?: ResolutionPreset;
  aspectRatio?: AspectRatio;
  frameRate?: FrameRate;
  bitrate?: number; // in kbps
  quality?: 'low' | 'medium' | 'high' | 'ultra';
}

/** Media file metadata */
export interface MediaMetadata {
  id: ID;
  name: string;
  path: string;
  type: MediaType;
  duration?: Time;
  width?: number;
  height?: number;
  frameRate?: number;
  fileSize: number;
  createdAt: Date;
  modifiedAt: Date;
  thumbnailPath?: string;
  tags?: string[];
}

/** AI Provider types */
export enum AIProviderType {
  LOCAL = 'local',
  CLOUD = 'cloud'
}

/** Local AI model configuration */
export interface LocalModelConfig {
  provider: AIProviderType.LOCAL;
  modelId: string; // e.g., 'gemma-3', 'llama-3.2'
  runtime: 'ollama' | 'llama-cpp' | 'onnx';
  quantization?: string; // e.g., 'q4_k_m', 'q8_0'
  contextLength?: number;
  gpuLayers?: number;
}

/** Cloud AI provider configuration */
export interface CloudProviderConfig {
  provider: AIProviderType.CLOUD;
  providerName: string; // e.g., 'gemini', 'openai', 'anthropic'
  apiKey?: string;
  modelId: string; // e.g., 'gemini-2.0', 'gpt-4o'
  endpoint?: string;
  maxTokens?: number;
  temperature?: number;
}

/** Unified AI Provider Configuration */
export type AIProviderConfig = LocalModelConfig | CloudProviderConfig;

/** AI Model capability flags */
export interface AICapabilities {
  textGeneration: boolean;
  imageGeneration: boolean;
  videoGeneration: boolean;
  audioProcessing: boolean;
  visionAnalysis: boolean;
  speechToText: boolean;
  textToSpeech: boolean;
  multiModal: boolean;
  streaming: boolean;
}

/** AI Model information */
export interface AIModelInfo {
  id: ID;
  name: string;
  provider: AIProviderConfig;
  capabilities: AICapabilities;
  isActive: boolean;
  isDefault: boolean;
  latency?: number; // ms
  costPerToken?: number; // USD
  lastUsed?: Date;
}

/** Agent types for specialized AI tasks */
export enum AgentType {
  DIRECTOR = 'director',
  EDITOR = 'editor',
  SUBTITLE = 'subtitle',
  COLORIST = 'colorist',
  AUDIO_ENGINEER = 'audio_engineer',
  MOTION_DESIGNER = 'motion_designer',
  PUBLISHING = 'publishing',
  RESEARCH = 'research'
}

/** Agent status */
export enum AgentStatus {
  IDLE = 'idle',
  THINKING = 'thinking',
  PLANNING = 'planning',
  EXECUTING = 'executing',
  WAITING = 'waiting',
  ERROR = 'error'
}

/** Agent state */
export interface AgentState {
  type: AgentType;
  status: AgentStatus;
  currentTask?: string;
  progress?: number; // 0-100
  error?: string;
}

/** Plugin manifest */
export interface PluginManifest {
  id: ID;
  name: string;
  version: string;
  description: string;
  author: string;
  entryPoint: string;
  capabilities: string[];
  permissions: string[];
  dependencies?: Record<string, string>;
  icon?: string;
}

/** Plugin instance */
export interface PluginInstance {
  manifest: PluginManifest;
  isEnabled: boolean;
  config: Record<string, unknown>;
  api?: unknown; // Plugin API instance
}

/** Editor adapter types */
export enum EditorType {
  CLIPCHAMP = 'clipchamp',
  PREMIERE = 'premiere',
  OPENSHOT = 'openshot',
  DAVINCI_RESOLVE = 'davinci_resolve',
  KDENLIVE = 'kdenlive',
  SHOTCUT = 'shotcut',
  OLIVE = 'olive',
  BLENDER = 'blender',
  OBS = 'obs'
}

/** Editor connection status */
export interface EditorConnectionStatus {
  type: EditorType;
  isConnected: boolean;
  version?: string;
  lastSync?: Date;
  error?: string;
}
