/**
 * Job Queue System for VID-ED X
 * 
 * Handles all long-running operations in background to keep UI responsive:
 * - Rendering/Exporting
 * - Proxy generation
 * - Thumbnail generation
 * - Waveform generation
 * - Speech recognition
 * - AI planning and generation
 * - Metadata extraction
 * 
 * Job States:
 * Pending -> Running -> (Completed | Failed | Cancelled)
 * Failed jobs can be retried
 */

import { ID } from '@vid-ed-x/core';

/** Job status enumeration */
export enum JobStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  PAUSED = 'paused'
}

/** Job type enumeration */
export enum JobType {
  RENDER = 'render',
  PROXY_GENERATION = 'proxy_generation',
  THUMBNAIL_GENERATION = 'thumbnail_generation',
  WAVEFORM_GENERATION = 'waveform_generation',
  SPEECH_RECOGNITION = 'speech_recognition',
  SUBTITLE_GENERATION = 'subtitle_generation',
  AI_PLANNING = 'ai_planning',
  AI_IMAGE_GENERATION = 'ai_image_generation',
  AI_VIDEO_GENERATION = 'ai_video_generation',
  METADATA_EXTRACTION = 'metadata_extraction',
  EXPORT = 'export',
  FILE_IMPORT = 'file_import',
  CUSTOM = 'custom'
}

/** Job priority levels */
export enum JobPriority {
  LOW = 0,
  NORMAL = 1,
  HIGH = 2,
  CRITICAL = 3
}

/** Progress update from a running job */
export interface JobProgress {
  percentage: number; // 0-100
  message?: string;
  currentStep?: number;
  totalSteps?: number;
  estimatedTimeRemaining?: number; // seconds
}

/** Job result data */
export interface JobResult<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  outputPath?: string;
  metadata?: Record<string, any>;
}

/** Job definition */
export interface JobDefinition<T = any> {
  id: ID;
  type: JobType;
  priority: JobPriority;
  status: JobStatus;
  title: string;
  description?: string;
  payload: any; // Job-specific data
  progress: JobProgress;
  result?: JobResult<T>;
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  retryCount: number;
  maxRetries: number;
  canRetry: boolean;
  canCancel: boolean;
  canPause: boolean;
  workerId?: string;
}

/** Job handler function type */
export type JobHandler<T = any> = (
  payload: any,
  progressCallback: (progress: JobProgress) => void,
  cancelSignal: { cancelled: boolean }
) => Promise<JobResult<T>>;

/** Job queue configuration */
export interface JobQueueConfig {
  maxConcurrentJobs: number;
  maxRetries: number;
  retryDelay: number; // ms
  persistJobs: boolean;
  storagePath?: string;
}

/** Default configuration */
const DEFAULT_CONFIG: JobQueueConfig = {
  maxConcurrentJobs: 2, // Conservative for low-end hardware
  maxRetries: 2,
  retryDelay: 1000,
  persistJobs: false
};

/**
 * Job Queue Manager
 * 
 * Manages execution of background jobs with priority scheduling,
 * progress tracking, and automatic retry logic.
 */
export class JobQueue {
  private jobs: Map<ID, JobDefinition> = new Map();
  private handlers: Map<JobType, JobHandler> = new Map();
  private config: JobQueueConfig;
  private runningJobs: Set<ID> = new Set();
  private cancelSignals: Map<ID, { cancelled: boolean }> = new Map();
  private listeners: Set<(job: JobDefinition) => void> = new Set();
  private processing: boolean = false;

  constructor(config: Partial<JobQueueConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Register a job handler for a specific job type
   */
  registerHandler(type: JobType, handler: JobHandler): void {
    this.handlers.set(type, handler);
  }

  /**
   * Add a new job to the queue
   */
  addJob<T = any>(
    type: JobType,
    title: string,
    payload: any,
    options: {
      priority?: JobPriority;
      description?: string;
      maxRetries?: number;
      canCancel?: boolean;
      canPause?: boolean;
    } = {}
  ): ID {
    const id = this.generateJobId();
    
    const job: JobDefinition<T> = {
      id,
      type,
      priority: options.priority ?? JobPriority.NORMAL,
      status: JobStatus.PENDING,
      title,
      description: options.description,
      payload,
      progress: {
        percentage: 0,
        message: 'Queued'
      },
      createdAt: new Date(),
      retryCount: 0,
      maxRetries: options.maxRetries ?? this.config.maxRetries,
      canRetry: true,
      canCancel: options.canCancel ?? true,
      canPause: options.canPause ?? false
    };

    this.jobs.set(id, job);
    this.cancelSignals.set(id, { cancelled: false });

    this.emitUpdate(job);
    this.scheduleProcessing();

    return id;
  }

  /**
   * Get job by ID
   */
  getJob(id: ID): JobDefinition | undefined {
    return this.jobs.get(id);
  }

  /**
   * Get all jobs
   */
  getAllJobs(): JobDefinition[] {
    return Array.from(this.jobs.values());
  }

  /**
   * Get jobs by status
   */
  getJobsByStatus(status: JobStatus): JobDefinition[] {
    return this.getAllJobs().filter(job => job.status === status);
  }

  /**
   * Get pending jobs sorted by priority
   */
  getPendingJobs(): JobDefinition[] {
    return this.getJobsByStatus(JobStatus.PENDING)
      .sort((a, b) => b.priority - a.priority || a.createdAt.getTime() - b.createdAt.getTime());
  }

  /**
   * Get running jobs
   */
  getRunningJobs(): JobDefinition[] {
    return this.getJobsByStatus(JobStatus.RUNNING);
  }

  /**
   * Cancel a job
   */
  cancelJob(id: ID): boolean {
    const job = this.jobs.get(id);
    if (!job || !job.canCancel) return false;

    if (job.status === JobStatus.RUNNING) {
      const signal = this.cancelSignals.get(id);
      if (signal) {
        signal.cancelled = true;
      }
    }

    job.status = JobStatus.CANCELLED;
    job.completedAt = new Date();
    job.progress.message = 'Cancelled';

    this.runningJobs.delete(id);
    this.emitUpdate(job);
    this.scheduleProcessing();

    return true;
  }

  /**
   * Retry a failed job
   */
  retryJob(id: ID): boolean {
    const job = this.jobs.get(id);
    if (!job || job.status !== JobStatus.FAILED || !job.canRetry) return false;

    if (job.retryCount >= job.maxRetries) {
      job.canRetry = false;
      return false;
    }

    job.status = JobStatus.PENDING;
    job.retryCount++;
    job.result = undefined;
    job.completedAt = undefined;
    job.startedAt = undefined;
    job.progress = { percentage: 0, message: 'Retrying' };

    this.emitUpdate(job);
    this.scheduleProcessing();

    return true;
  }

  /**
   * Pause a job (if supported)
   */
  pauseJob(id: ID): boolean {
    const job = this.jobs.get(id);
    if (!job || !job.canPause) return false;

    if (job.status === JobStatus.RUNNING) {
      // Signal pause - handler should check periodically
      job.status = JobStatus.PAUSED;
      this.runningJobs.delete(id);
      this.emitUpdate(job);
      this.scheduleProcessing();
      return true;
    }

    return false;
  }

  /**
   * Resume a paused job
   */
  resumeJob(id: ID): boolean {
    const job = this.jobs.get(id);
    if (!job || job.status !== JobStatus.PAUSED) return false;

    job.status = JobStatus.PENDING;
    this.emitUpdate(job);
    this.scheduleProcessing();

    return true;
  }

  /**
   * Clear completed jobs
   */
  clearCompleted(): number {
    let count = 0;
    for (const [id, job] of this.jobs.entries()) {
      if ([JobStatus.COMPLETED, JobStatus.CANCELLED].includes(job.status)) {
        this.jobs.delete(id);
        this.cancelSignals.delete(id);
        count++;
      }
    }
    return count;
  }

  /**
   * Subscribe to job updates
   */
  subscribe(listener: (job: JobDefinition) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /**
   * Wait for job completion
   */
  async waitForJob(id: ID, timeout?: number): Promise<JobDefinition> {
    return new Promise((resolve, reject) => {
      const job = this.jobs.get(id);
      if (!job) {
        reject(new Error(`Job ${id} not found`));
        return;
      }

      if ([JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED].includes(job.status)) {
        resolve(job);
        return;
      }

      const unsubscribe = this.subscribe((updatedJob) => {
        if (updatedJob.id === id && 
            [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED].includes(updatedJob.status)) {
          unsubscribe();
          resolve(updatedJob);
        }
      });

      if (timeout) {
        setTimeout(() => {
          unsubscribe();
          reject(new Error('Job timeout'));
        }, timeout);
      }
    });
  }

  /**
   * Schedule processing of pending jobs
   */
  private scheduleProcessing(): void {
    if (this.processing) return;
    
    this.processing = true;
    setImmediate(() => this.processQueue());
  }

  /**
   * Process the job queue
   */
  private async processQueue(): Promise<void> {
    while (this.runningJobs.size < this.config.maxConcurrentJobs) {
      const pendingJobs = this.getPendingJobs();
      if (pendingJobs.length === 0) break;

      const job = pendingJobs[0];
      await this.runJob(job);
    }

    this.processing = false;
  }

  /**
   * Run a single job
   */
  private async runJob(job: JobDefinition): Promise<void> {
    const handler = this.handlers.get(job.type);
    if (!handler) {
      job.status = JobStatus.FAILED;
      job.result = { success: false, error: `No handler registered for job type: ${job.type}` };
      job.completedAt = new Date();
      this.emitUpdate(job);
      return;
    }

    job.status = JobStatus.RUNNING;
    job.startedAt = new Date();
    this.runningJobs.add(job.id);
    this.emitUpdate(job);

    const cancelSignal = this.cancelSignals.get(job.id) || { cancelled: false };

    try {
      const progressCallback = (progress: JobProgress) => {
        if (job.status === JobStatus.RUNNING) {
          job.progress = progress;
          this.emitUpdate(job);
        }
      };

      const result = await handler(job.payload, progressCallback, cancelSignal);

      if (cancelSignal.cancelled) {
        job.status = JobStatus.CANCELLED;
        job.completedAt = new Date();
        job.progress.message = 'Cancelled';
      } else if (result.success) {
        job.status = JobStatus.COMPLETED;
        job.result = result;
        job.completedAt = new Date();
        job.progress.percentage = 100;
        job.progress.message = 'Completed';
      } else {
        throw new Error(result.error || 'Job failed');
      }
    } catch (error) {
      console.error(`Job ${job.id} failed:`, error);
      
      if (job.retryCount < job.maxRetries && !cancelSignal.cancelled) {
        // Schedule retry
        job.status = JobStatus.PENDING;
        job.retryCount++;
        job.progress.message = `Retry ${job.retryCount}/${job.maxRetries}`;
        
        setTimeout(() => {
          this.scheduleProcessing();
        }, this.config.retryDelay);
      } else {
        job.status = JobStatus.FAILED;
        job.result = { 
          success: false, 
          error: (error as Error).message 
        };
        job.completedAt = new Date();
        job.canRetry = false;
      }
    } finally {
      this.runningJobs.delete(job.id);
      this.cancelSignals.delete(job.id);
      this.emitUpdate(job);
      this.scheduleProcessing();
    }
  }

  /**
   * Emit job update to listeners
   */
  private emitUpdate(job: JobDefinition): void {
    for (const listener of this.listeners) {
      try {
        listener(job);
      } catch (error) {
        console.error('Job listener error:', error);
      }
    }
  }

  /**
   * Generate unique job ID
   */
  private generateJobId(): ID {
    return `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get queue statistics
   */
  getStats(): {
    total: number;
    pending: number;
    running: number;
    completed: number;
    failed: number;
    cancelled: number;
  } {
    const jobs = this.getAllJobs();
    return {
      total: jobs.length,
      pending: jobs.filter(j => j.status === JobStatus.PENDING).length,
      running: jobs.filter(j => j.status === JobStatus.RUNNING).length,
      completed: jobs.filter(j => j.status === JobStatus.COMPLETED).length,
      failed: jobs.filter(j => j.status === JobStatus.FAILED).length,
      cancelled: jobs.filter(j => j.status === JobStatus.CANCELLED).length
    };
  }
}

// Singleton instance
let globalJobQueue: JobQueue | null = null;

export function getJobQueue(config?: Partial<JobQueueConfig>): JobQueue {
  if (!globalJobQueue) {
    globalJobQueue = new JobQueue(config);
  }
  return globalJobQueue;
}

export function resetJobQueue(): void {
  globalJobQueue = null;
}
