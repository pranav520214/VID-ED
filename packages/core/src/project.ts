/**
 * Universal Project Format for VID-ED X
 * 
 * This module defines the editor-independent project representation
 * that allows interoperability between different video editors.
 */

import { ID, Time, TimeRange, MediaType, ExportFormat, AspectRatio } from './types';

/** Track types in the timeline */
export enum TrackType {
  VIDEO = 'video',
  AUDIO = 'audio',
  SUBTITLE = 'subtitle',
  GRAPHICS = 'graphics',
  EFFECTS = 'effects'
}

/** Clip types */
export enum ClipType {
  MEDIA = 'media',      // Video or audio file
  IMAGE = 'image',      // Static image
  TEXT = 'text',        // Text overlay
  SHAPE = 'shape',      // Shape/graphics
  TRANSITION = 'transition',
  EFFECT = 'effect',
  GENERATIVE = 'generative' // AI-generated content
}

/** Base clip properties */
export interface BaseClip {
  id: ID;
  type: ClipType;
  name: string;
  trackId: ID;
  startTime: Time;      // Position on timeline (seconds)
  duration: Time;       // Length of clip (seconds)
  inPoint: Time;        // Start point within source media
  outPoint: Time;       // End point within source media
  isEnabled: boolean;
  isLocked: boolean;
  opacity?: number;     // 0-1
  volume?: number;      // 0-1
  transform?: Transform;
  effects?: EffectInstance[];
  markers?: Marker[];
  metadata?: Record<string, unknown>;
}

/** Spatial transform for clips */
export interface Transform {
  position: { x: number; y: number };
  scale: number;
  rotation: number;
  anchorPoint: { x: number; y: number };
  flipHorizontal?: boolean;
  flipVertical?: boolean;
}

/** Video clip specific properties */
export interface VideoClip extends BaseClip {
  type: ClipType.MEDIA;
  mediaType: MediaType.VIDEO;
  sourcePath: string;
  speed?: number;       // Playback speed multiplier
  reverse?: boolean;
  colorGrading?: ColorGrading;
}

/** Audio clip specific properties */
export interface AudioClip extends BaseClip {
  type: ClipType.MEDIA;
  mediaType: MediaType.AUDIO;
  sourcePath: string;
  audioChannels?: 'mono' | 'stereo' | '5.1' | '7.1';
  fadeOut?: Time;
  fadeIn?: Time;
}

/** Image clip properties */
export interface ImageClip extends BaseClip {
  type: ClipType.IMAGE;
  sourcePath: string;
  fitMode?: 'fill' | 'fit' | 'stretch' | 'cover';
  kenBurnsEffect?: KenBurnsEffect;
}

/** Ken Burns effect (pan and zoom) */
export interface KenBurnsEffect {
  startScale: number;
  endScale: number;
  startPosition?: { x: number; y: number };
  endPosition?: { x: number; y: number };
}

/** Text clip properties */
export interface TextClip extends BaseClip {
  type: ClipType.TEXT;
  text: string;
  fontFamily?: string;
  fontSize?: number;
  fontWeight?: string;
  color?: string;
  backgroundColor?: string;
  alignment?: 'left' | 'center' | 'right';
  stroke?: TextStroke;
  shadow?: TextShadow;
  animation?: TextAnimation;
}

export interface TextStroke {
  color: string;
  width: number;
}

export interface TextShadow {
  color: string;
  offsetX: number;
  offsetY: number;
  blur: number;
}

export interface TextAnimation {
  type: 'fadeIn' | 'fadeOut' | 'typewriter' | 'slideIn' | 'bounce';
  duration: Time;
  delay?: Time;
}

/** Transition clip */
export interface TransitionClip extends BaseClip {
  type: ClipType.TRANSITION;
  transitionType: TransitionType;
  duration: Time;
  parameters?: Record<string, number>;
}

export enum TransitionType {
  CUT = 'cut',
  FADE = 'fade',
  CROSSFADE = 'crossfade',
  DISSOLVE = 'dissolve',
  WIPE = 'wipe',
  SLIDE = 'slide',
  ZOOM = 'zoom',
  BLUR = 'blur',
  MORPH = 'morph'
}

/** Effect instance on a clip */
export interface EffectInstance {
  id: ID;
  effectType: string;
  name: string;
  parameters: Record<string, unknown>;
  isEnabled: boolean;
  keyframes?: Keyframe[];
}

/** Keyframe for animation */
export interface Keyframe {
  time: Time;
  value: number | string;
  interpolation?: 'linear' | 'ease-in' | 'ease-out' | 'bezier';
  bezierIn?: { x: number; y: number };
  bezierOut?: { x: number; y: number };
}

/** Color grading settings */
export interface ColorGrading {
  exposure?: number;
  contrast?: number;
  highlights?: number;
  shadows?: number;
  whites?: number;
  blacks?: number;
  temperature?: number;
  tint?: number;
  saturation?: number;
  vibrance?: number;
  curves?: {
    rgb?: Array<{ input: number; output: number }>;
    red?: Array<{ input: number; output: number }>;
    green?: Array<{ input: number; output: number }>;
    blue?: Array<{ input: number; output: number }>;
  };
  lut?: string; // Path to LUT file
}

/** Marker on timeline or clip */
export interface Marker {
  id: ID;
  time: Time;
  name?: string;
  description?: string;
  color?: string;
  duration?: Time;
  metadata?: Record<string, unknown>;
}

/** Track in the timeline */
export interface Track {
  id: ID;
  type: TrackType;
  name: string;
  index: number;
  isEnabled: boolean;
  isMuted?: boolean;      // For audio tracks
  isSolo?: boolean;       // For audio tracks
  isVisible?: boolean;    // For video tracks
  isLocked: boolean;
  height?: number;        // UI track height
  clips: BaseClip[];
  effects?: EffectInstance[];
}

/** Sequence (main timeline container) */
export interface Sequence {
  id: ID;
  name: string;
  width: number;
  height: number;
  frameRate: number;
  aspectRatio: AspectRatio;
  startTimeCode?: string; // e.g., "00:00:00:00"
  tracks: Track[];
  markers: Marker[];
  workAreaStart?: Time;
  workAreaEnd?: Time;
}

/** Project root structure */
export interface Project {
  id: ID;
  name: string;
  version: string;
  createdAt: Date;
  modifiedAt: Date;
  sequences: Sequence[];
  activeSequenceId: ID;
  mediaLibrary: MediaItem[];
  assets: Asset[];
  exportPresets: ExportPreset[];
  settings: ProjectSettings;
  metadata?: Record<string, unknown>;
}

/** Media library item */
export interface MediaItem {
  id: ID;
  name: string;
  path: string;
  type: MediaType;
  duration?: Time;
  width?: number;
  height?: number;
  frameRate?: number;
  fileSize: number;
  thumbnailPath?: string;
  tags?: string[];
  bins?: string[]; // Folder/bin organization
  dateCreated: Date;
  dateModified: Date;
  dateImported: Date;
}

/** Asset (generated or imported) */
export interface Asset {
  id: ID;
  name: string;
  type: 'template' | 'preset' | 'luts' | 'graphics' | 'audio' | 'font';
  path: string;
  category?: string;
  tags?: string[];
  thumbnailPath?: string;
}

/** Export preset configuration */
export interface ExportPreset {
  id: ID;
  name: string;
  format: ExportFormat;
  isDefault: boolean;
  category?: 'social' | 'web' | 'broadcast' | 'archive';
}

/** Project-wide settings */
export interface ProjectSettings {
  autoSave: boolean;
  autoSaveInterval: number; // minutes
  proxyEnabled: boolean;
  proxyResolution?: string;
  renderQuality: 'draft' | 'high' | 'maximum';
  gpuAcceleration: boolean;
  scratchDiskPath?: string;
  cachePath?: string;
}

/** Bin/folder for organizing media */
export interface Bin {
  id: ID;
  name: string;
  parentId?: ID;
  children: Bin[];
  items: MediaItem[];
}
