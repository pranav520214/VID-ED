/**
 * Provider Manager
 * 
 * Manages multiple AI providers with support for:
 * - Enabling/disabling local and cloud providers
 * - Configuring API keys
 * - Selecting default providers
 * - Fallback ordering
 * - Usage monitoring
 * - Latency tracking
 */

import { ID, AIProviderConfig, AIProviderType, AIModelInfo, AICapabilities } from '@vid-ed-x/core';
import { IAIProvider, ProviderStatus, ProviderEvent, ProviderEventListener, ProviderEventType, ChatMessage, GenerationOptions, GenerationResponse } from './types';

/** Provider manager configuration */
export interface ProviderManagerConfig {
  defaultProviderId?: ID;
  fallbackOrder: ID[];
  autoFailover: boolean;
  maxRetries: number;
  requestTimeout: number; // ms
}

/** Provider registry entry */
interface ProviderRegistryEntry {
  provider: IAIProvider;
  isEnabled: boolean;
  isDefault: boolean;
  lastLatency?: number;
  totalRequests: number;
  failedRequests: number;
  lastUsed?: Date;
}

/** Usage statistics for a provider */
export interface ProviderUsageStats {
  providerId: ID;
  providerName: string;
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  averageLatency: number;
  totalTokens?: number;
  estimatedCost?: number; // USD
  lastUsed?: Date;
}

/** Default configuration */
const DEFAULT_CONFIG: ProviderManagerConfig = {
  fallbackOrder: [],
  autoFailover: true,
  maxRetries: 3,
  requestTimeout: 60000
};

/**
 * Provider Manager Class
 * 
 * Central hub for managing all AI providers in VID-ED X.
 * Handles provider registration, selection, failover, and monitoring.
 */
export class ProviderManager {
  private providers: Map<ID, ProviderRegistryEntry> = new Map();
  private config: ProviderManagerConfig;
  private listeners: Set<ProviderEventListener> = new Set();
  private currentDefaultId?: ID;

  constructor(config: Partial<ProviderManagerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Register a new provider
   */
  register(provider: IAIProvider, options: { enabled?: boolean; default?: boolean } = {}): void {
    if (this.providers.has(provider.id)) {
      throw new Error(`Provider with ID ${provider.id} is already registered`);
    }

    const entry: ProviderRegistryEntry = {
      provider,
      isEnabled: options.enabled ?? true,
      isDefault: options.default ?? false,
      totalRequests: 0,
      failedRequests: 0
    };

    this.providers.set(provider.id, entry);

    if (entry.isDefault) {
      this.currentDefaultId = provider.id;
    }

    this.emitEvent({
      type: ProviderEventType.MODEL_LOADED,
      providerId: provider.id,
      timestamp: new Date()
    });
  }

  /**
   * Unregister a provider
   */
  async unregister(providerId: ID): Promise<void> {
    const entry = this.providers.get(providerId);
    if (!entry) {
      throw new Error(`Provider ${providerId} not found`);
    }

    await entry.provider.dispose();
    this.providers.delete(providerId);

    if (this.currentDefaultId === providerId) {
      this.currentDefaultId = undefined;
    }

    this.emitEvent({
      type: ProviderEventType.MODEL_UNLOADED,
      providerId,
      timestamp: new Date()
    });
  }

  /**
   * Get a provider by ID
   */
  getProvider(providerId: ID): IAIProvider | undefined {
    return this.providers.get(providerId)?.provider;
  }

  /**
   * Get the default provider
   */
  getDefaultProvider(): IAIProvider | undefined {
    if (this.currentDefaultId) {
      const entry = this.providers.get(this.currentDefaultId);
      if (entry?.isEnabled) {
        return entry.provider;
      }
    }

    // Find first enabled provider
    for (const [id, entry] of this.providers) {
      if (entry.isEnabled) {
        return entry.provider;
      }
    }

    return undefined;
  }

  /**
   * Set the default provider
   */
  setDefaultProvider(providerId: ID): void {
    if (!this.providers.has(providerId)) {
      throw new Error(`Provider ${providerId} not found`);
    }

    // Update all entries
    for (const [id, entry] of this.providers) {
      entry.isDefault = id === providerId;
    }

    this.currentDefaultId = providerId;
  }

  /**
   * Enable or disable a provider
   */
  setProviderEnabled(providerId: ID, enabled: boolean): void {
    const entry = this.providers.get(providerId);
    if (!entry) {
      throw new Error(`Provider ${providerId} not found`);
    }

    entry.isEnabled = enabled;

    this.emitEvent({
      type: ProviderEventType.STATUS_CHANGE,
      providerId,
      timestamp: new Date(),
      data: { enabled }
    });
  }

  /**
   * Get all registered providers
   */
  getAllProviders(): Array<{ id: ID; name: string; type: AIProviderType; status: ProviderStatus; isEnabled: boolean }> {
    const result: Array<{ id: ID; name: string; type: AIProviderType; status: ProviderStatus; isEnabled: boolean }> = [];

    for (const [id, entry] of this.providers) {
      result.push({
        id,
        name: entry.provider.name,
        type: entry.provider.type as AIProviderType,
        status: entry.provider.status,
        isEnabled: entry.isEnabled
      });
    }

    return result;
  }

  /**
   * Get enabled providers
   */
  getEnabledProviders(): IAIProvider[] {
    const result: IAIProvider[] = [];

    for (const [, entry] of this.providers) {
      if (entry.isEnabled) {
        result.push(entry.provider);
      }
    }

    return result;
  }

  /**
   * Initialize all enabled providers
   */
  async initializeAll(): Promise<void> {
    const promises: Promise<void>[] = [];

    for (const [, entry] of this.providers) {
      if (entry.isEnabled) {
        promises.push(entry.provider.initialize());
      }
    }

    await Promise.all(promises);
  }

  /**
   * Dispose all providers
   */
  async disposeAll(): Promise<void> {
    const promises: Promise<void>[] = [];

    for (const [, entry] of this.providers) {
      promises.push(entry.provider.dispose());
    }

    await Promise.all(promises);
    this.providers.clear();
  }

  /**
   * Send a chat request with automatic failover
   */
  async chat(
    messages: ChatMessage[],
    options?: GenerationOptions,
    providerId?: ID
  ): Promise<GenerationResponse> {
    const targetProvider = providerId 
      ? this.getProvider(providerId)
      : this.getDefaultProvider();

    if (!targetProvider) {
      throw new Error('No available provider');
    }

    return this.executeWithFailover(
      async () => {
        const startTime = Date.now();
        const response = await targetProvider.chat(messages, options);
        const latency = Date.now() - startTime;

        this.updateProviderStats(targetProvider.id, { success: true, latency });
        return response;
      },
      targetProvider.id,
      options?.maxRetries ?? this.config.maxRetries
    );
  }

  /**
   * Execute a provider request with failover support
   */
  private async executeWithFailover<T>(
    fn: () => Promise<T>,
    primaryProviderId: ID,
    maxRetries: number
  ): Promise<T> {
    let lastError: Error | null = null;
    const attemptedProviders: Set<ID> = new Set();

    // Build provider order: primary + fallbacks
    const providerOrder: ID[] = [primaryProviderId];
    
    if (this.config.autoFailover && this.config.fallbackOrder.length > 0) {
      for (const fallbackId of this.config.fallbackOrder) {
        if (fallbackId !== primaryProviderId) {
          providerOrder.push(fallbackId);
        }
      }
    }

    // Try each provider in order
    for (let attempt = 0; attempt <= maxRetries && attempt < providerOrder.length; attempt++) {
      const providerId = providerOrder[attempt % providerOrder.length];
      
      if (attemptedProviders.has(providerId)) {
        continue;
      }
      attemptedProviders.add(providerId);

      const provider = this.getProvider(providerId);
      if (!provider || !this.providers.get(providerId)?.isEnabled) {
        continue;
      }

      try {
        return await fn();
      } catch (error) {
        lastError = error as Error;
        this.updateProviderStats(providerId, { success: false });
        
        console.warn(`Provider ${providerId} failed (attempt ${attempt + 1}):`, error);
        
        if (!this.config.autoFailover) {
          break;
        }
      }
    }

    throw lastError || new Error('All providers failed');
  }

  /**
   * Update provider statistics
   */
  private updateProviderStats(
    providerId: ID,
    stats: { success: boolean; latency?: number }
  ): void {
    const entry = this.providers.get(providerId);
    if (!entry) return;

    entry.totalRequests++;
    entry.lastUsed = new Date();

    if (stats.success) {
      entry.lastLatency = stats.latency;
    } else {
      entry.failedRequests++;
    }
  }

  /**
   * Get usage statistics for all providers
   */
  getUsageStats(): ProviderUsageStats[] {
    const stats: ProviderUsageStats[] = [];

    for (const [id, entry] of this.providers) {
      stats.push({
        providerId: id,
        providerName: entry.provider.name,
        totalRequests: entry.totalRequests,
        successfulRequests: entry.totalRequests - entry.failedRequests,
        failedRequests: entry.failedRequests,
        averageLatency: entry.lastLatency ?? 0,
        lastUsed: entry.lastUsed
      });
    }

    return stats;
  }

  /**
   * Test connection to a provider
   */
  async testConnection(providerId: ID): Promise<{ success: boolean; latency?: number; error?: string }> {
    const provider = this.getProvider(providerId);
    if (!provider) {
      return { success: false, error: 'Provider not found' };
    }

    try {
      const startTime = Date.now();
      const health = await provider.healthCheck();
      const latency = Date.now() - startTime;

      return {
        success: health.isHealthy,
        latency,
        error: health.error
      };
    } catch (error) {
      return {
        success: false,
        error: (error as Error).message
      };
    }
  }

  /**
   * Subscribe to provider events
   */
  subscribe(listener: ProviderEventListener): () => void {
    this.listeners.add(listener);

    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Emit an event to all listeners
   */
  private emitEvent(event: ProviderEvent): void {
    for (const listener of this.listeners) {
      try {
        listener(event);
      } catch (error) {
        console.error('Provider event listener error:', error);
      }
    }
  }
}

// Singleton instance
let globalProviderManager: ProviderManager | null = null;

export function getProviderManager(): ProviderManager {
  if (!globalProviderManager) {
    globalProviderManager = new ProviderManager();
  }
  return globalProviderManager;
}

export function resetProviderManager(): void {
  globalProviderManager = null;
}
