/**
 * MCP Client Types
 */

import { ID } from '@vid-ed-x/core';

/** MCP Server types supported by VID-ED X */
export enum MCPServerType {
  VIDEO = 'video-mcp',
  AUDIO = 'audio-mcp',
  VISION = 'vision-mcp',
  SPEECH = 'speech-mcp',
  SUBTITLE = 'subtitle-mcp',
  FILESYSTEM = 'filesystem-mcp',
  TIMELINE = 'timeline-mcp',
  EFFECTS = 'effects-mcp',
  EXPORT = 'export-mcp',
  PLUGIN = 'plugin-mcp',
  PROVIDER = 'provider-mcp'
}

/** Connection transport type */
export enum TransportType {
  STDIO = 'stdio',
  HTTP = 'http',
  WEBSOCKET = 'websocket',
  IPC = 'ipc'
}

/** Server connection configuration */
export interface MCPServerConfig {
  id: ID;
  name: string;
  type: MCPServerType;
  transport: TransportType;
  command?: string; // For stdio transport
  args?: string[];
  url?: string; // For http/websocket transport
  env?: Record<string, string>;
  timeout?: number; // ms
  autoStart?: boolean;
}

/** Tool input schema definition */
export interface ToolInputSchema {
  type: 'object';
  properties: Record<string, {
    type: string;
    description?: string;
    required?: boolean;
    enum?: string[];
    default?: unknown;
  }>;
  required?: string[];
}

/** Tool definition from MCP server */
export interface MCPTool {
  name: string;
  description: string;
  inputSchema: ToolInputSchema;
  serverId: ID;
}

/** Tool execution result */
export interface ToolResult {
  success: boolean;
  data?: unknown;
  error?: string;
  metadata?: Record<string, unknown>;
}

/** Resource from MCP server */
export interface MCPResource {
  uri: string;
  name: string;
  description?: string;
  mimeType?: string;
}

/** Prompt template from MCP server */
export interface MCPPrompt {
  name: string;
  description?: string;
  arguments?: Array<{
    name: string;
    description?: string;
    required?: boolean;
  }>;
}

/** Server status */
export enum MCPServerStatus {
  STOPPED = 'stopped',
  STARTING = 'starting',
  CONNECTED = 'connected',
  ERROR = 'error',
  DISCONNECTED = 'disconnected'
}

/** Server health information */
export interface ServerHealth {
  status: MCPServerStatus;
  latency?: number; // ms
  lastError?: string;
  uptime?: number; // seconds
  toolCount?: number;
  resourceCount?: number;
  promptCount?: number;
}

/** Notification from MCP server */
export interface MCPNotification {
  method: string;
  params?: Record<string, unknown>;
  serverId: ID;
  timestamp: Date;
}

/** Progress update during tool execution */
export interface ProgressUpdate {
  progress: number; // 0-100
  total?: number;
  message?: string;
  stage?: string;
}

/** MCP Client options */
export interface MCPClientOptions {
  debugMode: boolean;
  defaultTimeout: number; // ms
  maxRetries: number;
  retryDelay: number; // ms
  logNotifications: boolean;
}

/** Event types for MCP client */
export enum MCPEventType {
  SERVER_CONNECTED = 'server_connected',
  SERVER_DISCONNECTED = 'server_disconnected',
  SERVER_ERROR = 'server_error',
  TOOL_REGISTERED = 'tool_registered',
  TOOL_UNREGISTERED = 'tool_unregistered',
  NOTIFICATION_RECEIVED = 'notification_received',
  PROGRESS_UPDATE = 'progress_update'
}

/** MCP Client event */
export interface MCPEvent {
  type: MCPEventType;
  serverId?: ID;
  toolName?: string;
  data?: unknown;
  timestamp: Date;
  error?: Error;
}

/** Event listener type */
export type MCPEventListener = (event: MCPEvent) => void;
