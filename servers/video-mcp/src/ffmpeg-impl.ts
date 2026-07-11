/**
 * Video MCP Server - FFmpeg Implementation
 * 
 * This module provides the actual FFmpeg-based implementations
 * for all video processing tools.
 * 
 * Dependencies:
 * - fluent-ffmpeg: https://github.com/fluent-ffmpeg/node-fluent-ffmpeg
 * - FFmpeg must be installed on the system
 */

import ffmpeg from 'fluent-ffmpeg';
import fs from 'fs/promises';
import path from 'path';
import {
  TrimVideoInput,
  ConcatenateVideosInput,
  ExtractAudioInput,
  GetMediaInfoInput,
  GenerateThumbnailInput,
  ChangeSpeedInput,
  ReverseVideoInput,
  ScaleVideoInput,
  ConvertFormatInput,
  CreateColorBarsInput
} from './tools';

/**
 * Ensure output directory exists
 */
async function ensureOutputDir(outputPath: string): Promise<void> {
  const dir = path.dirname(outputPath);
  await fs.mkdir(dir, { recursive: true });
}

/**
 * Check if input file exists
 */
async function validateInputFile(inputPath: string): Promise<void> {
  try {
    await fs.access(inputPath, fs.constants.R_OK);
  } catch {
    throw new Error(`Input file not found or not readable: ${inputPath}`);
  }
}

/**
 * Trim a video file to specified in/out points
 * Uses stream copy when possible for fast operation
 */
export async function trimVideo(params: TrimVideoInput): Promise<{ outputPath: string; duration: number }> {
  await validateInputFile(params.inputPath);
  await ensureOutputDir(params.outputPath);

  return new Promise((resolve, reject) => {
    const command = ffmpeg(params.inputPath)
      .setStartTime(params.inPoint)
      .setDuration(params.outPoint - params.inPoint);

    if (params.codec === 'copy') {
      command.videoCodec('copy').audioCodec('copy');
    } else {
      command.videoCodec(params.codec === 'prores' ? 'prores_ks' : params.codec);
    }

    command
      .save(params.outputPath)
      .on('end', () => {
        resolve({
          outputPath: params.outputPath,
          duration: params.outPoint - params.inPoint
        });
      })
      .on('error', (err) => {
        reject(new Error(`FFmpeg error: ${err.message}`));
      });
  });
}

/**
 * Concatenate multiple video files
 * Note: All videos must have same codec/format for stream copy
 */
export async function concatenateVideos(params: ConcatenateVideosInput): Promise<{ outputPath: string }> {
  // Validate all input files
  for (const inputPath of params.inputPaths) {
    await validateInputFile(inputPath);
  }
  await ensureOutputDir(params.outputPath);

  return new Promise((resolve, reject) => {
    const command = ffmpeg();

    // Add all inputs
    params.inputPaths.forEach(inputPath => {
      command.input(inputPath);
    });

    if (params.codec === 'copy') {
      // For stream copy, use concat demuxer approach
      // This requires creating a temporary concat file
      reject(new Error('Stream copy concatenation requires different implementation. Use re-encoding or see documentation.'));
      return;
    }

    command
      .videoCodec(params.codec === 'prores' ? 'prores_ks' : params.codec)
      .audioCodec('aac')
      .mergeToFile(params.outputPath)
      .on('end', () => {
        resolve({ outputPath: params.outputPath });
      })
      .on('error', (err) => {
        reject(new Error(`FFmpeg error: ${err.message}`));
      });
  });
}

/**
 * Extract audio track from video
 */
export async function extractAudio(params: ExtractAudioInput): Promise<{ outputPath: string }> {
  await validateInputFile(params.inputPath);
  await ensureOutputDir(params.outputPath);

  return new Promise((resolve, reject) => {
    const command = ffmpeg(params.inputPath).noVideo();

    if (params.audioCodec === 'copy') {
      command.audioCodec('copy');
    } else {
      command.audioCodec(params.audioCodec);
    }

    command
      .save(params.outputPath)
      .on('end', () => {
        resolve({ outputPath: params.outputPath });
      })
      .on('error', (err) => {
        reject(new Error(`FFmpeg error: ${err.message}`));
      });
  });
}

/**
 * Get detailed media information using ffprobe
 */
export async function getMediaInfo(params: GetMediaInfoInput): Promise<{
  duration: number;
  width: number;
  height: number;
  frameRate: number;
  videoCodec: string;
  audioCodec?: string;
  fileSize: number;
  bitRate?: number;
}> {
  await validateInputFile(params.inputPath);

  return new Promise((resolve, reject) => {
    ffmpeg.ffprobe(params.inputPath, (err, metadata) => {
      if (err) {
        reject(new Error(`FFprobe error: ${err.message}`));
        return;
      }

      const videoStream = metadata.streams.find(s => s.codec_type === 'video');
      const audioStream = metadata.streams.find(s => s.codec_type === 'audio');

      if (!videoStream) {
        reject(new Error('No video stream found in file'));
        return;
      }

      // Calculate framerate
      let frameRate = 0;
      if (videoStream.r_frame_rate) {
        const [num, den] = videoStream.r_frame_rate.split('/').map(Number);
        frameRate = num / den;
      }

      resolve({
        duration: metadata.format.duration || 0,
        width: videoStream.width || 0,
        height: videoStream.height || 0,
        frameRate,
        videoCodec: videoStream.codec_name || 'unknown',
        audioCodec: audioStream?.codec_name,
        fileSize: metadata.format.size || 0,
        bitRate: metadata.format.bit_rate ? parseInt(metadata.format.bit_rate) : undefined
      });
    });
  });
}

/**
 * Generate thumbnail from video at specific time position
 */
export async function generateThumbnail(params: GenerateThumbnailInput): Promise<{ outputPath: string }> {
  await validateInputFile(params.inputPath);
  await ensureOutputDir(params.outputPath);

  return new Promise((resolve, reject) => {
    ffmpeg(params.inputPath)
      .seek(params.timePosition)
      .frames(1)
      .size(`${params.width}x${params.height}`)
      .save(params.outputPath)
      .on('end', () => {
        resolve({ outputPath: params.outputPath });
      })
      .on('error', (err) => {
        reject(new Error(`FFmpeg error: ${err.message}`));
      });
  });
}

/**
 * Change video playback speed
 */
export async function changeSpeed(params: ChangeSpeedInput): Promise<{ outputPath: string }> {
  await validateInputFile(params.inputPath);
  await ensureOutputDir(params.outputPath);

  return new Promise((resolve, reject) => {
    const command = ffmpeg(params.inputPath);

    // Video speed filter
    const videoFilter = `setpts=${1 / params.speedMultiplier}*PTS`;
    
    if (params.audioPitch) {
      // Preserve audio pitch with atempo filter
      // atempo only supports 0.5-2.0, so we may need to chain filters
      const audioSpeed = params.speedMultiplier;
      let audioFilter = `atempo=${audioSpeed}`;
      
      // For speeds outside 0.5-2.0 range, we'd need to chain multiple atempo filters
      // This is a simplified implementation
      if (audioSpeed < 0.5 || audioSpeed > 2.0) {
        console.warn('Audio speed outside optimal range, quality may be affected');
      }

      command.videoFilter(videoFilter).audioFilter(audioFilter);
    } else {
      command.videoFilter(videoFilter);
    }

    command
      .videoCodec('h264')
      .audioCodec('aac')
      .save(params.outputPath)
      .on('end', () => {
        resolve({ outputPath: params.outputPath });
      })
      .on('error', (err) => {
        reject(new Error(`FFmpeg error: ${err.message}`));
      });
  });
}

/**
 * Reverse video playback
 * Note: This requires two passes and can be slow
 */
export async function reverseVideo(params: ReverseVideoInput): Promise<{ outputPath: string }> {
  await validateInputFile(params.inputPath);
  await ensureOutputDir(params.outputPath);

  return new Promise((resolve, reject) => {
    ffmpeg(params.inputPath)
      .videoFilter('reverse')
      .audioFilter('areverse')
      .videoCodec('h264')
      .audioCodec('aac')
      .save(params.outputPath)
      .on('end', () => {
        resolve({ outputPath: params.outputPath });
      })
      .on('error', (err) => {
        reject(new Error(`FFmpeg error: ${err.message}`));
      });
  });
}

/**
 * Scale/resize video to different dimensions
 */
export async function scaleVideo(params: ScaleVideoInput): Promise<{ outputPath: string }> {
  await validateInputFile(params.inputPath);
  await ensureOutputDir(params.outputPath);

  return new Promise((resolve, reject) => {
    const command = ffmpeg(params.inputPath);

    let scaleFilter: string;
    
    if (params.maintainAspectRatio) {
      if (params.width && params.height) {
        scaleFilter = `scale=${params.width}:${params.height}`;
      } else if (params.width) {
        scaleFilter = `scale=${params.width}:-1`;
      } else if (params.height) {
        scaleFilter = `scale=-1:${params.height}`;
      } else {
        reject(new Error('At least width or height must be specified'));
        return;
      }
    } else {
      scaleFilter = `scale=${params.width || 0}:${params.height || 0}`;
    }

    command
      .videoFilter(scaleFilter)
      .videoCodec(params.codec)
      .audioCodec('copy')
      .save(params.outputPath)
      .on('end', () => {
        resolve({ outputPath: params.outputPath });
      })
      .on('error', (err) => {
        reject(new Error(`FFmpeg error: ${err.message}`));
      });
  });
}

/**
 * Convert video to different format/container
 */
export async function convertFormat(params: ConvertFormatInput): Promise<{ outputPath: string }> {
  await validateInputFile(params.inputPath);
  await ensureOutputDir(params.outputPath);

  return new Promise((resolve, reject) => {
    const command = ffmpeg(params.inputPath);

    // Set video codec
    if (params.videoCodec) {
      const codec = params.videoCodec === 'prores' ? 'prores_ks' : params.videoCodec;
      command.videoCodec(codec);
      
      // Set quality parameters for certain codecs
      if (params.crf !== undefined && ['h264', 'h265', 'av1', 'vp9'].includes(params.videoCodec)) {
        command.outputOption(`-crf ${params.crf}`);
      }
    }

    // Set audio codec
    if (params.audioCodec) {
      command.audioCodec(params.audioCodec);
    }

    // Set bitrate if specified
    if (params.bitrate) {
      command.outputOption(`-b:v ${params.bitrate}k`);
    }

    command
      .toFormat(params.container)
      .save(params.outputPath)
      .on('end', () => {
        resolve({ outputPath: params.outputPath });
      })
      .on('error', (err) => {
        reject(new Error(`FFmpeg error: ${err.message}`));
      });
  });
}

/**
 * Create color bar test pattern video
 */
export async function createColorBars(params: CreateColorBarsInput): Promise<{ outputPath: string }> {
  await ensureOutputDir(params.outputPath);

  return new Promise((resolve, reject) => {
    ffmpeg()
      .inputOptions([
        `-f lavfi`,
        `-i testsrc=duration=${params.duration}:size=${params.width}x${params.height}:rate=${params.frameRate}`,
        `-f lavfi`,
        `-i sine=frequency=1000:duration=${params.duration}`
      ])
      .videoCodec('h264')
      .audioCodec('aac')
      .save(params.outputPath)
      .on('end', () => {
        resolve({ outputPath: params.outputPath });
      })
      .on('error', (err) => {
        reject(new Error(`FFmpeg error: ${err.message}`));
      });
  });
}

// Export all tool implementations
export const VideoTools = {
  trimVideo,
  concatenateVideos,
  extractAudio,
  getMediaInfo,
  generateThumbnail,
  changeSpeed,
  reverseVideo,
  scaleVideo,
  convertFormat,
  createColorBars
};
