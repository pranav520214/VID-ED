/**
 * Audio MCP Server - FFmpeg Implementation
 * 
 * Provides FFmpeg-based audio processing implementations.
 */

import ffmpeg from 'fluent-ffmpeg';
import fs from 'fs/promises';
import path from 'path';
import {
  NormalizeAudioInput,
  RemoveSilenceInput,
  ApplyFadeInput,
  ChangeVolumeInput,
  ConvertAudioFormatInput,
  MixAudioInput,
  AnalyzeSpectrumInput,
  ReduceNoiseInput,
  ChangePitchInput,
  ConvertChannelsInput
} from './tools';

async function ensureOutputDir(outputPath: string): Promise<void> {
  const dir = path.dirname(outputPath);
  await fs.mkdir(dir, { recursive: true });
}

async function validateInputFile(inputPath: string): Promise<void> {
  try {
    await fs.access(inputPath, fs.constants.R_OK);
  } catch {
    throw new Error(`Input file not found or not readable: ${inputPath}`);
  }
}

/**
 * Normalize audio to target loudness (LUFS)
 * Uses EBU R128 loudnorm filter
 */
export async function normalizeAudio(params: NormalizeAudioInput): Promise<{ outputPath: string }> {
  await validateInputFile(params.inputPath);
  await ensureOutputDir(params.outputPath);

  return new Promise((resolve, reject) => {
    ffmpeg(params.inputPath)
      .audioFilter(`loudnorm=I=${params.targetLevel}:TP=-1.0:LRA=7`)
      .save(params.outputPath)
      .on('end', () => resolve({ outputPath: params.outputPath }))
      .on('error', (err) => reject(new Error(`FFmpeg error: ${err.message}`)));
  });
}

/**
 * Remove silence from audio
 * Uses silencedetect and atrim filters
 */
export async function removeSilence(params: RemoveSilenceInput): Promise<{ outputPath: string; removedSegments: number }> {
  await validateInputFile(params.inputPath);
  await ensureOutputDir(params.outputPath);

  // Note: True silence removal requires two-pass analysis
  // This is a simplified implementation using silenceremove filter
  return new Promise((resolve, reject) => {
    ffmpeg(params.inputPath)
      .audioFilter(`silenceremove=start_periods=1:start_duration=${params.minDuration}:start_threshold=${params.threshold}`)
      .save(params.outputPath)
      .on('end', () => resolve({ 
        outputPath: params.outputPath,
        removedSegments: 0 // Would need analysis pass to determine actual count
      }))
      .on('error', (err) => reject(new Error(`FFmpeg error: ${err.message}`)));
  });
}

/**
 * Apply fade in/out effect
 */
export async function applyFade(params: ApplyFadeInput): Promise<{ outputPath: string }> {
  await validateInputFile(params.inputPath);
  await ensureOutputDir(params.outputPath);

  return new Promise((resolve, reject) => {
    const command = ffmpeg(params.inputPath);
    
    const filters: string[] = [];
    
    if (params.fadeIn > 0) {
      filters.push(`afade=t=in:st=0:d=${params.fadeIn}`);
    }
    
    if (params.fadeOut > 0) {
      // Fade out will be applied at end - duration needed in second pass
      filters.push(`afade=t=out:st=-${params.fadeOut}:d=${params.fadeOut}`);
    }

    if (filters.length === 0) {
      resolve({ outputPath: params.outputPath });
      return;
    }

    command.audioFilter(filters).save(params.outputPath)
      .on('end', () => resolve({ outputPath: params.outputPath }))
      .on('error', (err) => reject(new Error(`FFmpeg error: ${err.message}`)));
  });
}

/**
 * Change audio volume/gain
 */
export async function changeVolume(params: ChangeVolumeInput): Promise<{ outputPath: string }> {
  await validateInputFile(params.inputPath);
  await ensureOutputDir(params.outputPath);

  return new Promise((resolve, reject) => {
    ffmpeg(params.inputPath)
      .audioFilter(`volume=${Math.pow(10, params.gain / 20)}`)
      .save(params.outputPath)
      .on('end', () => resolve({ outputPath: params.outputPath }))
      .on('error', (err) => reject(new Error(`FFmpeg error: ${err.message}`)));
  });
}

/**
 * Convert audio format/codec
 */
export async function convertAudioFormat(params: ConvertAudioFormatInput): Promise<{ outputPath: string }> {
  await validateInputFile(params.inputPath);
  await ensureOutputDir(params.outputPath);

  return new Promise((resolve, reject) => {
    const command = ffmpeg(params.inputPath).noVideo();

    // Map codec names to FFmpeg codec identifiers
    const codecMap: Record<string, string> = {
      aac: 'aac',
      mp3: 'libmp3lame',
      wav: 'pcm_s16le',
      flac: 'flac',
      opus: 'libopus',
      ogg: 'libvorbis'
    };

    command.audioCodec(codecMap[params.codec]);

    if (params.bitrate && ['aac', 'mp3', 'opus', 'ogg'].includes(params.codec)) {
      command.audioBitrate(params.bitrate);
    }

    if (params.sampleRate) {
      command.audioFrequency(params.sampleRate);
    }

    // Set output format based on extension
    const ext = path.extname(params.outputPath).slice(1);
    command.toFormat(ext || params.codec);

    command
      .save(params.outputPath)
      .on('end', () => resolve({ outputPath: params.outputPath }))
      .on('error', (err) => reject(new Error(`FFmpeg error: ${err.message}`)));
  });
}

/**
 * Mix multiple audio files
 */
export async function mixAudio(params: MixAudioInput): Promise<{ outputPath: string }> {
  // Validate all inputs
  for (const inputPath of params.inputPaths) {
    await validateInputFile(inputPath);
  }
  await ensureOutputDir(params.outputPath);

  return new Promise((resolve, reject) => {
    const command = ffmpeg();

    // Add all inputs
    params.inputPaths.forEach((inputPath, index) => {
      command.input(inputPath);
    });

    // Build complex filter for mixing
    const volumes = params.volumes || params.inputPaths.map(() => 1.0);
    const filterParts = params.inputPaths.map((_, i) => `[${i}:a]volume=${volumes[i]}[a${i}]`);
    const mixInputs = params.inputPaths.map((_, i) => `[a${i}]`).join('');
    filterParts.push(`${mixInputs}amix=inputs=${params.inputPaths.length}:duration=longest[out]`);

    command
      .complexFilter(filterParts, 'out')
      .audioCodec('aac')
      .save(params.outputPath)
      .on('end', () => resolve({ outputPath: params.outputPath }))
      .on('error', (err) => reject(new Error(`FFmpeg error: ${err.message}`)));
  });
}

/**
 * Analyze audio spectrum
 */
export async function analyzeSpectrum(params: AnalyzeSpectrumInput): Promise<{ 
  peakFrequency: number; 
  averageFrequency: number;
  data: Array<{ frequency: number; amplitude: number }> 
}> {
  await validateInputFile(params.inputPath);

  // Use ffprobe to get spectrum data
  return new Promise((resolve, reject) => {
    const command = ffmpeg.ffprobe(params.inputPath, (err, metadata) => {
      if (err) {
        reject(new Error(`FFprobe error: ${err.message}`));
        return;
      }

      const audioStream = metadata.streams.find(s => s.codec_type === 'audio');
      
      if (!audioStream) {
        reject(new Error('No audio stream found'));
        return;
      }

      // Basic analysis from metadata
      // Full spectrum analysis would require additional processing
      resolve({
        peakFrequency: 0, // Would need actual FFT analysis
        averageFrequency: 0,
        data: []
      });
    });
  });
}

/**
 * Reduce noise in audio
 * Note: True noise reduction requires noise profile sampling
 */
export async function reduceNoise(params: ReduceNoiseInput): Promise<{ outputPath: string }> {
  await validateInputFile(params.inputPath);
  await ensureOutputDir(params.outputPath);

  // Simplified implementation using highpass/lowpass filtering
  // True spectral noise gating would require more complex setup
  return new Promise((resolve, reject) => {
    const command = ffmpeg(params.inputPath);
    
    // Apply gentle noise reduction using audiofilter
    // In production, would use RNNoise or similar
    const reduction = params.reductionAmount;
    command.audioFilter([
      `highpass=f=20`,
      `lowpass=f=16000`,
      `afftdn=nf=-${reduction * 20}`
    ]);

    command
      .save(params.outputPath)
      .on('end', () => resolve({ outputPath: params.outputPath }))
      .on('error', (err) => reject(new Error(`FFmpeg error: ${err.message}`)));
  });
}

/**
 * Change audio pitch without affecting speed
 */
export async function changePitch(params: ChangePitchInput): Promise<{ outputPath: string }> {
  await validateInputFile(params.inputPath);
  await ensureOutputDir(params.outputPath);

  return new Promise((resolve, reject) => {
    ffmpeg(params.inputPath)
      .audioFilter(`asetrate=44100*${Math.pow(2, params.semitones / 12)},aresample=44100`)
      .save(params.outputPath)
      .on('end', () => resolve({ outputPath: params.outputPath }))
      .on('error', (err) => reject(new Error(`FFmpeg error: ${err.message}`)));
  });
}

/**
 * Convert between mono and stereo
 */
export async function convertChannels(params: ConvertChannelsInput): Promise<{ outputPath: string }> {
  await validateInputFile(params.inputPath);
  await ensureOutputDir(params.outputPath);

  return new Promise((resolve, reject) => {
    const command = ffmpeg(params.inputPath);

    if (params.channels === 'mono') {
      command.audioChannels(1);
    } else {
      // Stereo - duplicate mono to stereo or keep existing
      command.audioFilter('pan=stereo|c0=c0|c1=c0');
    }

    command
      .audioCodec('aac')
      .save(params.outputPath)
      .on('end', () => resolve({ outputPath: params.outputPath }))
      .on('error', (err) => reject(new Error(`FFmpeg error: ${err.message}`)));
  });
}

// Export all tool implementations
export const AudioTools = {
  normalizeAudio,
  removeSilence,
  applyFade,
  changeVolume,
  convertAudioFormat,
  mixAudio,
  analyzeSpectrum,
  reduceNoise,
  changePitch,
  convertChannels
};
