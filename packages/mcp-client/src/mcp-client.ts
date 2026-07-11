/**
 * MCP Client Implementation
 * 
 * Handles connections to MCP servers and tool execution.
 */

import { ID } from '@vid-ed-x/core';
import {
  MCPServerConfig,
  MCPServerType,
  TransportType,
  MCPTool,
  ToolResult,
  MCPResource,
  MCPPrompt,
  MCPServerStatus,
  ServerHealth,
  MCPClientOptions,
  MCPEvent,
  MCPEventType,
  MCPEventListener,
  ProgressUpdate
} from './types';

/** Default client options */
const DEFAULT_OPTIONS: MCPClientOptions = {
  debugMode: false,
  defaultTimeout: 30000,
  maxRetries: 3,
  retryDelay: 1000,
  logNotifications: true
};

/**
 * MCP Client Class
 * 
 * Manages connections to multiple MCP servers and provides
 * a unified interface for tool execution.
 */
export class MCPClient {
  private servers: Map<ID, MCPServerConfig> = new Map();
  private serverStatuses: Map<ID, MCPServerStatus> = new Map();
  private tools: Map<string, MCPTool> = new Map(); // key: serverId:toolName
  private resources: Map<string, MCPResource> = new Map();
  private prompts: Map<string, MCPPrompt> = new Map();
  private listeners: Set<MCPEventListener> = new Set();
  private options: MCPClientOptions;

  constructor(options: Partial<MCPClientOptions> = {}) {
    this.options = { ...DEFAULT_OPTIONS, ...options };
  }

  /**
   * Register an MCP server configuration
   */
  registerServer(config: MCPServerConfig): void {
    if (this.servers.has(config.id)) {
      throw new Error(`Server ${config.id} is already registered`);
    }

    this.servers.set(config.id, config);
    this.serverStatuses.set(config.id, MCPServerStatus.STOPPED);

    if (config.autoStart) {
      this.connectServer(config.id).catch(console.error);
    }
  }

  /**
   * Connect to an MCP server
   */
  async connectServer(serverId: ID): Promise<void> {
    const config = this.servers.get(serverId);
    if (!config) {
      throw new Error(`Server ${serverId} not found`);
    }

    this.setServerStatus(serverId, MCPServerStatus.STARTING);

    try {
      // Connection logic would be implemented here
      // For now, simulate connection
      await this.simulateConnection(config);

      this.setServerStatus(serverId, MCPServerStatus.CONNECTED);
      this.emitEvent({
        type: MCPEventType.SERVER_CONNECTED,
        serverId,
        timestamp: new Date()
      });

      // Discover tools, resources, and prompts
      await this.discoverCapabilities(serverId);
    } catch (error) {
      this.setServerStatus(serverId, MCPServerStatus.ERROR);
      this.emitEvent({
        type: MCPEventType.SERVER_ERROR,
        serverId,
        timestamp: new Date(),
        error: error as Error
      });
      throw error;
    }
  }

  /**
   * Disconnect from an MCP server
   */
  async disconnectServer(serverId: ID): Promise<void> {
    const config = this.servers.get(serverId);
    if (!config) {
      return;
    }

    // Remove tools from this server
    for (const [key] of this.tools) {
      if (key.startsWith(`${serverId}:`)) {
        this.tools.delete(key);
      }
    }

    this.setServerStatus(serverId, MCPServerStatus.DISCONNECTED);
    this.emitEvent({
      type: MCPEventType.SERVER_DISCONNECTED,
      serverId,
      timestamp: new Date()
    });
  }

  /**
   * Get server status
   */
  getServerStatus(serverId: ID): MCPServerStatus {
    return this.serverStatuses.get(serverId) ?? MCPServerStatus.STOPPED;
  }

  /**
   * Get all connected servers
   */
  getConnectedServers(): ID[] {
    const result: ID[] = [];
    for (const [id, status] of this.serverStatuses) {
      if (status === MCPServerStatus.CONNECTED) {
        result.push(id);
      }
    }
    return result;
  }

  /**
   * Get available tools
   */
  getTools(serverId?: ID): MCPTool[] {
    const allTools = Array.from(this.tools.values());
    if (serverId) {
      return allTools.filter(tool => tool.serverId === serverId);
    }
    return allTools;
  }

  /**
   * Execute a tool on an MCP server
   */
  async executeTool(
    serverId: ID,
    toolName: string,
    args: Record<string, unknown>,
    onProgress?: (progress: ProgressUpdate) => void
  ): Promise<ToolResult> {
    const status = this.getServerStatus(serverId);
    if (status !== MCPServerStatus.CONNECTED) {
      return {
        success: false,
        error: `Server ${serverId} is not connected (status: ${status})`
      };
    }

    const toolKey = `${serverId}:${toolName}`;
    const tool = this.tools.get(toolKey);
    if (!tool) {
      return {
        success: false,
        error: `Tool ${toolName} not found on server ${serverId}`
      };
    }

    try {
      // Validate arguments against schema
      this.validateToolArgs(args, tool.inputSchema);

      // Execute the tool
      const result = await this.executeToolImpl(serverId, toolName, args, onProgress);

      return {
        success: true,
        data: result.data,
        metadata: result.metadata
      };
    } catch (error) {
      return {
        success: false,
        error: (error as Error).message
      };
    }
  }

  /**
   * List available resources
   */
  getResources(serverId?: ID): MCPResource[] {
    const allResources = Array.from(this.resources.values());
    if (serverId) {
      // Resources don't have serverId in their structure, so we'd need to track it separately
      return allResources;
    }
    return allResources;
  }

  /**
   * List available prompts
   */
  getPrompts(serverId?: ID): MCPPrompt[] {
    const allPrompts = Array.from(this.prompts.values());
    if (serverId) {
      return allPrompts;
    }
    return allPrompts;
  }

  /**
   * Get server health information
   */
  getServerHealth(serverId: ID): ServerHealth {
    const status = this.getServerStatus(serverId);
    const serverTools = this.getTools(serverId);

    return {
      status,
      toolCount: serverTools.length,
      resourceCount: 0,
      promptCount: 0
    };
  }

  /**
   * Subscribe to MCP events
   */
  subscribe(listener: MCPEventListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /**
   * Set server status and emit event
   */
  private setServerStatus(serverId: ID, status: MCPServerStatus): void {
    this.serverStatuses.set(serverId, status);
  }

  /**
   * Emit an event to all listeners
   */
  private emitEvent(event: MCPEvent): void {
    for (const listener of this.listeners) {
      try {
        listener(event);
      } catch (error) {
        console.error('MCP event listener error:', error);
      }
    }
  }

  /**
   * Simulate server connection (placeholder for real implementation)
   */
  private async simulateConnection(config: MCPServerConfig): Promise<void> {
    // In a real implementation, this would:
    // - Start stdio processes
    // - Establish HTTP/WebSocket connections
    // - Perform handshake
    // - Initialize the MCP protocol
    
    return new Promise(resolve => setTimeout(resolve, 100));
  }

  /**
   * Discover tools, resources, and prompts from a server
   */
  private async discoverCapabilities(serverId: ID): Promise<void> {
    // In a real implementation, this would call the MCP initialize/list_tools endpoints
    // For now, this is a placeholder
  }

  /**
   * Validate tool arguments against input schema
   */
  private validateToolArgs(
    args: Record<string, unknown>,
    schema: ToolInputSchema
  ): void {
    const required = schema.required || [];
    
    for (const req of required) {
      if (!(req in args)) {
        throw new Error(`Missing required argument: ${req}`);
      }
    }

    for (const [key, value] of Object.entries(args)) {
      const propSchema = schema.properties[key];
      if (!propSchema) {
        continue; // Unknown property, may be allowed
      }

      const actualType = typeof value;
      const expectedType = propSchema.type;

      if (expectedType === 'string' && actualType !== 'string') {
        throw new Error(`Argument ${key} must be a string`);
      }
      if (expectedType === 'number' && actualType !== 'number') {
        throw new Error(`Argument ${key} must be a number`);
      }
      if (expectedType === 'boolean' && actualType !== 'boolean') {
        throw new Error(`Argument ${key} must be a boolean`);
      }
      if (expectedType === 'array' && !Array.isArray(value)) {
        throw new Error(`Argument ${key} must be an array`);
      }
      if (expectedType === 'object' && (actualType !== 'object' || value === null)) {
        throw new Error(`Argument ${key} must be an object`);
      }
    }
  }

  /**
   * Execute tool implementation (placeholder)
   */
  private async executeToolImpl(
    serverId: ID,
    toolName: string,
    args: Record<string, unknown>,
    onProgress?: (progress: ProgressUpdate) => void
  ): Promise<{ data: unknown; metadata?: Record<string, unknown> }> {
    // In a real implementation, this would send the request to the MCP server
    // and handle the response
    
    return {
      data: null,
      metadata: { serverId, toolName, executedAt: new Date().toISOString() }
    };
  }
}

// Singleton instance
let globalMCPClient: MCPClient | null = null;

export function getMCPClient(): MCPClient {
  if (!globalMCPClient) {
    globalMCPClient = new MCPClient();
  }
  return globalMCPClient;
}

export function resetMCPClient(): void {
  globalMCPClient = null;
}
