/**
 * Tool Registry for MCP Client
 * 
 * Centralized registry for discovering and managing tools across all MCP servers.
 */

import { ID } from '@vid-ed-x/core';
import { MCPTool, MCPServerType } from './types';

/**
 * Tool category for organization
 */
export enum ToolCategory {
  VIDEO_EDITING = 'video_editing',
  AUDIO_PROCESSING = 'audio_processing',
  SUBTITLES = 'subtitles',
  EFFECTS = 'effects',
  EXPORT = 'export',
  GENERATIVE_AI = 'generative_ai',
  FILESYSTEM = 'filesystem',
  ANALYSIS = 'analysis'
}

/**
 * Extended tool metadata
 */
export interface ToolMetadata extends MCPTool {
  category: ToolCategory;
  tags: string[];
  isExperimental: boolean;
  estimatedDuration?: 'fast' | 'medium' | 'slow';
  requiresConfirmation: boolean;
}

/**
 * Tool Registry Class
 * 
 * Provides centralized tool discovery, categorization, and search.
 */
export class ToolRegistry {
  private tools: Map<string, ToolMetadata> = new Map(); // key: serverId:toolName
  private categoryIndex: Map<ToolCategory, Set<string>> = new Map();
  private tagIndex: Map<string, Set<string>> = new Map();

  /**
   * Register a tool in the registry
   */
  register(tool: MCPTool, metadata: Partial<ToolMetadata> = {}): void {
    const key = `${tool.serverId}:${tool.name}`;
    
    const fullMetadata: ToolMetadata = {
      ...tool,
      category: metadata.category || ToolCategory.ANALYSIS,
      tags: metadata.tags || [],
      isExperimental: metadata.isExperimental || false,
      requiresConfirmation: metadata.requiresConfirmation || false,
      estimatedDuration: metadata.estimatedDuration
    };

    this.tools.set(key, fullMetadata);

    // Update category index
    if (!this.categoryIndex.has(fullMetadata.category)) {
      this.categoryIndex.set(fullMetadata.category, new Set());
    }
    this.categoryIndex.get(fullMetadata.category)!.add(key);

    // Update tag index
    for (const tag of fullMetadata.tags) {
      if (!this.tagIndex.has(tag)) {
        this.tagIndex.set(tag, new Set());
      }
      this.tagIndex.get(tag)!.add(key);
    }
  }

  /**
   * Unregister a tool
   */
  unregister(serverId: ID, toolName: string): void {
    const key = `${serverId}:${toolName}`;
    const tool = this.tools.get(key);
    
    if (tool) {
      // Remove from category index
      this.categoryIndex.get(tool.category)?.delete(key);
      
      // Remove from tag index
      for (const tag of tool.tags) {
        this.tagIndex.get(tag)?.delete(key);
      }
      
      this.tools.delete(key);
    }
  }

  /**
   * Get a tool by server ID and name
   */
  getTool(serverId: ID, toolName: string): ToolMetadata | undefined {
    return this.tools.get(`${serverId}:${toolName}`);
  }

  /**
   * Get all tools
   */
  getAllTools(): ToolMetadata[] {
    return Array.from(this.tools.values());
  }

  /**
   * Get tools by category
   */
  getToolsByCategory(category: ToolCategory): ToolMetadata[] {
    const keys = this.categoryIndex.get(category);
    if (!keys) return [];
    
    return Array.from(keys).map(key => this.tools.get(key)!).filter(Boolean);
  }

  /**
   * Get tools by tag
   */
  getToolsByTag(tag: string): ToolMetadata[] {
    const keys = this.tagIndex.get(tag);
    if (!keys) return [];
    
    return Array.from(keys).map(key => this.tools.get(key)!).filter(Boolean);
  }

  /**
   * Search tools by query
   */
  searchTools(query: string): ToolMetadata[] {
    const lowerQuery = query.toLowerCase();
    
    return this.getAllTools().filter(tool => {
      return (
        tool.name.toLowerCase().includes(lowerQuery) ||
        tool.description.toLowerCase().includes(lowerQuery) ||
        tool.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
      );
    });
  }

  /**
   * Get all categories with tool counts
   */
  getCategories(): Array<{ category: ToolCategory; count: number }> {
    const result: Array<{ category: ToolCategory; count: number }> = [];
    
    for (const [category, keys] of this.categoryIndex) {
      result.push({
        category,
        count: keys.size
      });
    }
    
    return result.sort((a, b) => b.count - a.count);
  }

  /**
   * Get all unique tags
   */
  getAllTags(): string[] {
    return Array.from(this.tagIndex.keys()).sort();
  }

  /**
   * Clear all registered tools
   */
  clear(): void {
    this.tools.clear();
    this.categoryIndex.clear();
    this.tagIndex.clear();
  }

  /**
   * Get tool count
   */
  getToolCount(): number {
    return this.tools.size;
  }
}

// Singleton instance
let globalToolRegistry: ToolRegistry | null = null;

export function getToolRegistry(): ToolRegistry {
  if (!globalToolRegistry) {
    globalToolRegistry = new ToolRegistry();
  }
  return globalToolRegistry;
}

export function resetToolRegistry(): void {
  globalToolRegistry = null;
}
