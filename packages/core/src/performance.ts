/**
 * VID-ED X Performance Optimization Architecture
 * 
 * This module implements performance-first design for low-end hardware:
 * - Intel Core i3 4th Gen / AMD Ryzen 3
 * - 4GB RAM minimum
 * - Integrated graphics support
 * - HDD storage support
 * 
 * Core Principles:
 * 1. Performance First - Editor must remain responsive
 * 2. Memory First - Keep RAM under 500MB idle, 1GB editing
 * 3. Battery First - Minimize CPU/GPU usage when possible
 * 4. AI Second - AI never blocks editing operations
 */

import { ID, Time } from '@vid-ed-x/core';

/**
 * Hardware capability detection
 */
export interface HardwareCapabilities {
  cpuCores: number;
  cpuSpeed: number; // GHz
  ramGB: number;
  gpuAvailable: boolean;
  gpuVRAM?: number; // GB
  gpuEncoder?: 'nvenc' | 'amf' | 'qsv' | 'none';
  isSSD: boolean;
  performanceTier: 'low' | 'medium' | 'high';
}

/**
 * Proxy resolution presets for low-end hardware
 */
export enum ProxyResolution {
  P240 = '240p',    // 426x240 - Minimum for preview
  P360 = '360p',    // 640x360 - Low-end default
  P540 = '540p',    // 960x540 - Mid-range
  P720 = '720p',    // 1280x720 - High-end proxy
  ORIGINAL = 'original' // Use original (not recommended for low-end)
}

/**
 * Adaptive quality settings for playback
 */
export interface PlaybackQualitySettings {
  targetFPS: number;
  maxResolution: ProxyResolution;
  skipFrames: boolean;
  dropQualityOnLag: boolean;
  qualitySteps: ProxyResolution[];
}

/**
 * Memory budget allocation
 */
export interface MemoryBudget {
  maxRAM_MB: number;
  thumbnailCache_MB: number;
  waveformCache_MB: number;
  proxyCache_MB: number;
  undoHistoryItems: number;
  preloadClips: number;
}

/**
 * Detect hardware capabilities
 */
export async function detectHardware(): Promise<HardwareCapabilities> {
  // CPU detection
  const cpuCores = navigator.hardwareConcurrency || 2;
  
  // RAM detection (in MB, convert to GB)
  let ramGB = 4; // Default minimum
  if ('deviceMemory' in navigator) {
    ramGB = (navigator as any).deviceMemory || 4;
  }
  
  // GPU detection
  let gpuAvailable = false;
  let gpuVRAM: number | undefined;
  let gpuEncoder: 'nvenc' | 'amf' | 'qsv' | 'none' = 'none';
  
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (gl) {
      gpuAvailable = true;
      
      // Get debug info for GPU detection
      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
      if (debugInfo) {
        const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
        
        // Detect encoder capability
        if (renderer?.includes('NVIDIA')) {
          gpuEncoder = 'nvenc';
        } else if (renderer?.includes('AMD') || renderer?.includes('Radeon')) {
          gpuEncoder = 'amf';
        } else if (renderer?.includes('Intel')) {
          gpuEncoder = 'qsv';
        }
      }
    }
  } catch (e) {
    console.warn('WebGL not available:', e);
  }
  
  // Storage type detection (best effort)
  // Note: Cannot reliably detect SSD vs HDD from browser
  // User should configure manually or we assume HDD for safety
  const isSSD = false; // Conservative default
  
  // Determine performance tier
  let performanceTier: 'low' | 'medium' | 'high' = 'low';
  if (ramGB >= 16 && cpuCores >= 8 && gpuAvailable) {
    performanceTier = 'high';
  } else if (ramGB >= 8 && cpuCores >= 4) {
    performanceTier = 'medium';
  }
  
  return {
    cpuCores,
    cpuSpeed: 2.0, // Cannot detect from JS, assume conservative
    ramGB,
    gpuAvailable,
    gpuVRAM,
    gpuEncoder,
    isSSD,
    performanceTier
  };
}

/**
 * Get memory budget based on hardware
 */
export function getMemoryBudget(hardware: HardwareCapabilities): MemoryBudget {
  if (hardware.performanceTier === 'low') {
    return {
      maxRAM_MB: 500,
      thumbnailCache_MB: 50,
      waveformCache_MB: 30,
      proxyCache_MB: 200,
      undoHistoryItems: 20,
      preloadClips: 3
    };
  } else if (hardware.performanceTier === 'medium') {
    return {
      maxRAM_MB: 1000,
      thumbnailCache_MB: 150,
      waveformCache_MB: 80,
      proxyCache_MB: 500,
      undoHistoryItems: 50,
      preloadClips: 5
    };
  } else {
    return {
      maxRAM_MB: 2000,
      thumbnailCache_MB: 300,
      waveformCache_MB: 150,
      proxyCache_MB: 1000,
      undoHistoryItems: 100,
      preloadClips: 10
    };
  }
}

/**
 * Get optimal proxy resolution for hardware
 */
export function getOptimalProxyResolution(hardware: HardwareCapabilities): ProxyResolution {
  switch (hardware.performanceTier) {
    case 'low':
      return ProxyResolution.P360;
    case 'medium':
      return ProxyResolution.P540;
    case 'high':
      return ProxyResolution.P720;
    default:
      return ProxyResolution.P360;
  }
}

/**
 * Get playback quality settings for hardware
 */
export function getPlaybackSettings(hardware: HardwareCapabilities): PlaybackQualitySettings {
  const baseResolution = getOptimalProxyResolution(hardware);
  
  return {
    targetFPS: hardware.performanceTier === 'high' ? 60 : 30,
    maxResolution: baseResolution,
    skipFrames: hardware.performanceTier !== 'high',
    dropQualityOnLag: true,
    qualitySteps: [
      ProxyResolution.P240,
      ProxyResolution.P360,
      ProxyResolution.P540,
      ProxyResolution.P720
    ].filter(r => {
      // Only include resolutions at or below max
      const resOrder = [
        ProxyResolution.P240,
        ProxyResolution.P360,
        ProxyResolution.P540,
        ProxyResolution.P720
      ];
      return resOrder.indexOf(r) <= resOrder.indexOf(baseResolution);
    })
  };
}

/**
 * Low-memory mode detection and configuration
 */
export interface LowMemoryModeConfig {
  enabled: boolean;
  disableShadows: boolean;
  disableBlur: boolean;
  reduceAnimations: boolean;
  smallThumbnailCache: boolean;
  aggressiveUnloading: boolean;
}

export function getLowMemoryMode(hardware: HardwareCapabilities): LowMemoryModeConfig {
  const isLowMemory = hardware.ramGB <= 4;
  
  return {
    enabled: isLowMemory,
    disableShadows: isLowMemory,
    disableBlur: isLowMemory,
    reduceAnimations: isLowMemory,
    smallThumbnailCache: isLowMemory,
    aggressiveUnloading: isLowMemory
  };
}

/**
 * Worker pool for background processing
 */
export class WorkerPool {
  private workers: Worker[] = [];
  private taskQueue: Array<{
    data: any;
    resolve: (result: any) => void;
    reject: (error: Error) => void;
  }> = [];
  private workerStatus: Array<{ busy: boolean; id: number }> = [];
  
  constructor(workerScript: string, numWorkers: number = 2) {
    for (let i = 0; i < numWorkers; i++) {
      const worker = new Worker(workerScript);
      worker.onmessage = (event) => this.handleWorkerMessage(i, event);
      worker.onerror = (error) => this.handleWorkerError(i, error);
      this.workers.push(worker);
      this.workerStatus.push({ busy: false, id: i });
    }
  }
  
  private handleWorkerMessage(workerId: number, event: MessageEvent) {
    const status = this.workerStatus[workerId];
    status.busy = false;
    
    // Process next task in queue
    this.processQueue();
  }
  
  private handleWorkerError(workerId: number, error: ErrorEvent) {
    console.error(`Worker ${workerId} error:`, error);
    const status = this.workerStatus[workerId];
    status.busy = false;
    this.processQueue();
  }
  
  private processQueue() {
    if (this.taskQueue.length === 0) return;
    
    const freeWorker = this.workerStatus.findIndex(s => !s.busy);
    if (freeWorker === -1) return;
    
    const task = this.taskQueue.shift()!;
    const worker = this.workers[freeWorker];
    
    this.workerStatus[freeWorker].busy = true;
    worker.postMessage(task.data);
  }
  
  public postTask(data: any): Promise<any> {
    return new Promise((resolve, reject) => {
      this.taskQueue.push({ data, resolve, reject });
      this.processQueue();
    });
  }
  
  public terminate() {
    this.workers.forEach(w => w.terminate());
    this.workers = [];
    this.taskQueue = [];
  }
}

/**
 * Performance monitoring
 */
export class PerformanceMonitor {
  private fpsHistory: number[] = [];
  private memoryUsageMB: number = 0;
  private frameCount = 0;
  private lastTime = performance.now();
  private callbacks: Set<(metrics: { fps: number; memoryMB: number }) => void> = new Set();
  
  start() {
    const measure = () => {
      const now = performance.now();
      const delta = now - this.lastTime;
      this.frameCount++;
      
      if (delta >= 1000) {
        const fps = Math.round((this.frameCount * 1000) / delta);
        this.fpsHistory.push(fps);
        if (this.fpsHistory.length > 10) {
          this.fpsHistory.shift();
        }
        
        // Get memory usage if available
        if ('memory' in performance) {
          this.memoryUsageMB = Math.round((performance as any).memory.usedJSHeapSize / (1024 * 1024));
        }
        
        const avgFPS = Math.round(this.fpsHistory.reduce((a, b) => a + b, 0) / this.fpsHistory.length);
        
        this.callbacks.forEach(cb => cb({ fps: avgFPS, memoryMB: this.memoryUsageMB }));
        
        this.frameCount = 0;
        this.lastTime = now;
      }
      
      requestAnimationFrame(measure);
    };
    
    requestAnimationFrame(measure);
  }
  
  subscribe(callback: (metrics: { fps: number; memoryMB: number }) => void): () => void {
    this.callbacks.add(callback);
    return () => this.callbacks.delete(callback);
  }
  
  getAverageFPS(): number {
    if (this.fpsHistory.length === 0) return 0;
    return Math.round(this.fpsHistory.reduce((a, b) => a + b, 0) / this.fpsHistory.length);
  }
  
  getMemoryUsage(): number {
    return this.memoryUsageMB;
  }
}

// Singleton instances
let perfMonitor: PerformanceMonitor | null = null;

export function getPerformanceMonitor(): PerformanceMonitor {
  if (!perfMonitor) {
    perfMonitor = new PerformanceMonitor();
    perfMonitor.start();
  }
  return perfMonitor;
}
