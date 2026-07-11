/**
 * AI Provider Types and Interfaces
 */

import { AIProviderConfig, AICapabilities, AIModelInfo, ID } from '@vid-ed-x/core';

/** Message role types */
export enum MessageRole {
  SYSTEM = 'system',
  USER = 'user',
  ASSISTANT = 'assistant'
}

/** Content types for messages */
export type ContentPart = 
  | { type: 'text'; text: string }
  | { type: 'image'; url: string; mimeType?: string }
  | { type: 'image_base64'; data: string; mimeType: string }
  | { type: 'video'; url: string }
  | { type: 'audio'; url: string };

/** Chat message structure */
export interface ChatMessage {
  role: MessageRole;
  content: string | ContentPart[];
  name?: string;
}

/** Generation options */
export interface GenerationOptions {
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  topK?: number;
  frequencyPenalty?: number;
  presencePenalty?: number;
  stopSequences?: string[];
  stream?: boolean;
  seed?: number;
}

/** Token usage information */
export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

/** Streaming chunk for real-time responses */
export interface StreamChunk {
  content?: string;
  finishReason?: 'stop' | 'length' | 'error' | null;
  usage?: TokenUsage;
}

/** Response from AI provider */
export interface GenerationResponse {
  id: ID;
  content: string;
  model: string;
  usage?: TokenUsage;
  finishReason?: string;
  createdAt: Date;
  rawResponse?: unknown; // Provider-specific raw response
}

/** Provider status */
export enum ProviderStatus {
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',
  LOADING = 'loading'
}

/** Provider health check result */
export interface HealthCheckResult {
  isHealthy: boolean;
  latency?: number; // ms
  error?: string;
  details?: Record<string, unknown>;
}

/** Base provider interface that all providers must implement */
export interface IAIProvider {
  /** Unique identifier for this provider instance */
  readonly id: ID;
  
  /** Human-readable name */
  readonly name: string;
  
  /** Provider type (local or cloud) */
  readonly type: AIProviderConfig['provider'];
  
  /** Current connection status */
  readonly status: ProviderStatus;
  
  /** Supported capabilities */
  readonly capabilities: AICapabilities;
  
  /** Model configuration */
  readonly config: AIProviderConfig;
  
  /**
   * Initialize the provider (load models, establish connections)
   */
  initialize(): Promise<void>;
  
  /**
   * Clean up resources
   */
  dispose(): Promise<void>;
  
  /**
   * Check if provider is healthy and responsive
   */
  healthCheck(): Promise<HealthCheckResult>;
  
  /**
   * Send a chat completion request
   */
  chat(
    messages: ChatMessage[],
    options?: GenerationOptions
  ): Promise<GenerationResponse>;
  
  /**
   * Stream a chat completion response
   */
  chatStream(
    messages: ChatMessage[],
    options?: GenerationOptions
  ): AsyncGenerator<StreamChunk>;
  
  /**
   * Generate an image from a text prompt
   */
  generateImage?(
    prompt: string,
    options?: ImageGenerationOptions
  ): Promise<ImageGenerationResponse>;
  
  /**
   * Generate video from text or image
   */
  generateVideo?(
    prompt: string,
    options?: VideoGenerationOptions
  ): Promise<VideoGenerationResponse>;
  
  /**
   * Analyze an image and return description/insights
   */
  analyzeImage?(
    imageUrl: string,
    prompt?: string
  ): Promise<string>;
  
  /**
   * Convert speech to text
   */
  speechToText?(
    audioUrl: string,
    options?: SpeechToTextOptions
  ): Promise<SpeechToTextResponse>;
  
  /**
   * Convert text to speech
   */
  textToSpeech?(
    text: string,
    options?: TextToSpeechOptions
  ): Promise<TextToSpeechResponse>;
}

/** Image generation options */
export interface ImageGenerationOptions {
  width?: number;
  height?: number;
  steps?: number;
  guidanceScale?: number;
  negativePrompt?: string;
  seed?: number;
  style?: string;
}

/** Image generation response */
export interface ImageGenerationResponse {
  id: ID;
  imageUrl: string;
  prompt: string;
  width: number;
  height: number;
  seed?: number;
  createdAt: Date;
}

/** Video generation options */
export interface VideoGenerationOptions {
  duration?: number; // seconds
  fps?: number;
  width?: number;
  height?: number;
  seed?: number;
}

/** Video generation response */
export interface VideoGenerationResponse {
  id: ID;
  videoUrl: string;
  thumbnailUrl?: string;
  prompt: string;
  duration: number;
  width: number;
  height: number;
  fps: number;
  createdAt: Date;
}

/** Speech-to-text options */
export interface SpeechToTextOptions {
  language?: string;
  timestampGranularity?: 'word' | 'segment';
  speakerDiarization?: boolean;
}

/** Speech-to-text response */
export interface SpeechToTextResponse {
  id: ID;
  text: string;
  language: string;
  segments?: TranscriptionSegment[];
  speakers?: SpeakerSegment[];
  duration: number;
}

export interface TranscriptionSegment {
  text: string;
  start: number;
  end: number;
  confidence?: number;
}

export interface SpeakerSegment {
  speaker: string;
  start: number;
  end: number;
  text: string;
}

/** Text-to-speech options */
export interface TextToSpeechOptions {
  voice?: string;
  language?: string;
  speed?: number;
  pitch?: number;
  format?: 'mp3' | 'wav' | 'ogg' | 'flac';
}

/** Text-to-speech response */
export interface TextToSpeechResponse {
  id: ID;
  audioUrl: string;
  text: string;
  voice: string;
  duration: number;
  format: string;
}

/** Provider event types */
export enum ProviderEventType {
  STATUS_CHANGE = 'status_change',
  MODEL_LOADED = 'model_loaded',
  MODEL_UNLOADED = 'model_unloaded',
  ERROR = 'error',
  STREAM_CHUNK = 'stream_chunk',
  GENERATION_COMPLETE = 'generation_complete'
}

/** Provider event */
export interface ProviderEvent {
  type: ProviderEventType;
  providerId: ID;
  timestamp: Date;
  data?: unknown;
}

/** Provider event listener */
export type ProviderEventListener = (event: ProviderEvent) => void;
