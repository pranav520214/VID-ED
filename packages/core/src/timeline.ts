/**
 * Timeline Utilities for VID-ED X
 */

import { Time, TimeRange } from './types';
import { Track, Sequence, BaseClip, Marker } from './project';

/**
 * Calculate the end time of a clip
 */
export function getClipEndTime(clip: BaseClip): Time {
  return clip.startTime + clip.duration;
}

/**
 * Check if two time ranges overlap
 */
export function doRangesOverlap(range1: TimeRange, range2: TimeRange): boolean {
  return range1.start < range2.end && range2.start < range1.end;
}

/**
 * Find overlapping clips in a track
 */
export function findOverlappingClips(clips: BaseClip[], targetClip: BaseClip): BaseClip[] {
  const targetRange: TimeRange = {
    start: targetClip.startTime,
    end: getClipEndTime(targetClip)
  };

  return clips.filter(clip => {
    if (clip.id === targetClip.id) return false;
    const clipRange: TimeRange = {
      start: clip.startTime,
      end: getClipEndTime(clip)
    };
    return doRangesOverlap(targetRange, clipRange);
  });
}

/**
 * Snap a time value to a grid (e.g., frame boundaries)
 */
export function snapToGrid(time: Time, frameRate: number, snapInterval?: number): Time {
  const interval = snapInterval || (1 / frameRate);
  return Math.round(time / interval) * interval;
}

/**
 * Convert seconds to SMPTE timecode format
 */
export function secondsToTimecode(seconds: Time, frameRate: number): string {
  const totalFrames = Math.floor(seconds * frameRate);
  const hours = Math.floor(totalFrames / (frameRate * 3600));
  const minutes = Math.floor((totalFrames % (frameRate * 3600)) / (frameRate * 60));
  const secs = Math.floor((totalFrames % (frameRate * 60)) / frameRate);
  const frames = totalFrames % frameRate;

  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}:${frames.toString().padStart(2, '0')}`;
}

/**
 * Convert SMPTE timecode to seconds
 */
export function timecodeToSeconds(timecode: string, frameRate: number): Time {
  const parts = timecode.split(':').map(Number);
  if (parts.length !== 4) {
    throw new Error(`Invalid timecode format: ${timecode}. Expected HH:MM:SS:FF`);
  }

  const [hours, minutes, seconds, frames] = parts;
  return hours * 3600 + minutes * 60 + seconds + frames / frameRate;
}

/**
 * Get the total duration of a sequence
 */
export function getSequenceDuration(sequence: Sequence): Time {
  if (sequence.tracks.length === 0) return 0;

  let maxEndTime = 0;
  for (const track of sequence.tracks) {
    for (const clip of track.clips) {
      const endTime = getClipEndTime(clip);
      if (endTime > maxEndTime) {
        maxEndTime = endTime;
      }
    }
  }

  return maxEndTime;
}

/**
 * Find the next edit point (clip boundary) after a given time
 */
export function findNextEditPoint(tracks: Track[], currentTime: Time): Time | null {
  const editPoints: Time[] = [];

  for (const track of tracks) {
    for (const clip of track.clips) {
      editPoints.push(clip.startTime);
      editPoints.push(getClipEndTime(clip));
    }
  }

  const nextPoint = editPoints.filter(t => t > currentTime).sort((a, b) => a - b)[0];
  return nextPoint ?? null;
}

/**
 * Find the previous edit point (clip boundary) before a given time
 */
export function findPreviousEditPoint(tracks: Track[], currentTime: Time): Time | null {
  const editPoints: Time[] = [];

  for (const track of tracks) {
    for (const clip of track.clips) {
      editPoints.push(clip.startTime);
      editPoints.push(getClipEndTime(clip));
    }
  }

  const prevPoint = editPoints.filter(t => t < currentTime).sort((a, b) => b - a)[0];
  return prevPoint ?? null;
}

/**
 * Ripple delete: remove a clip and shift all subsequent clips
 */
export function rippleDelete(tracks: Track[], clipId: string): Track[] {
  const resultTracks: Track[] = [];
  let deleteDuration = 0;
  let deleteStartTime = 0;

  // Find the clip to delete
  for (const track of tracks) {
    const clip = track.clips.find(c => c.id === clipId);
    if (clip) {
      deleteDuration = clip.duration;
      deleteStartTime = clip.startTime;
      break;
    }
  }

  if (deleteDuration === 0) return tracks;

  // Remove clip and shift subsequent clips
  for (const track of tracks) {
    const newClips = track.clips
      .filter(clip => clip.id !== clipId)
      .map(clip => {
        if (clip.startTime > deleteStartTime) {
          return { ...clip, startTime: clip.startTime - deleteDuration };
        }
        return clip;
      });

    resultTracks.push({ ...track, clips: newClips });
  }

  return resultTracks;
}

/**
 * Insert a gap at a specific time, shifting all subsequent clips
 */
export function insertGap(tracks: Track[], time: Time, gapDuration: Time): Track[] {
  const resultTracks: Track[] = [];

  for (const track of tracks) {
    const newClips = track.clips.map(clip => {
      if (clip.startTime >= time) {
        return { ...clip, startTime: clip.startTime + gapDuration };
      }
      return clip;
    });

    resultTracks.push({ ...track, clips: newClips });
  }

  return resultTracks;
}

/**
 * Find markers within a time range
 */
export function findMarkersInRange(markers: Marker[], range: TimeRange): Marker[] {
  return markers.filter(marker => {
    const markerEnd = marker.time + (marker.duration || 0);
    return marker.time < range.end && markerEnd > range.start;
  });
}

/**
 * Sort clips by their start time
 */
export function sortClipsByTime(clips: BaseClip[]): BaseClip[] {
  return [...clips].sort((a, b) => a.startTime - b.startTime);
}

/**
 * Calculate the bounding box of all clips in tracks
 */
export function getTimelineBounds(tracks: Track[]): { start: Time; end: Time } {
  let minStart = Infinity;
  let maxEnd = 0;

  for (const track of tracks) {
    for (const clip of track.clips) {
      if (clip.startTime < minStart) minStart = clip.startTime;
      const endTime = getClipEndTime(clip);
      if (endTime > maxEnd) maxEnd = endTime;
    }
  }

  if (minStart === Infinity) {
    return { start: 0, end: 0 };
  }

  return { start: minStart, end: maxEnd };
}
