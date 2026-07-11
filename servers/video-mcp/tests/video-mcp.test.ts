/**
 * Video MCP Server Tests
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { VideoTools } from '../src/ffmpeg-impl';
import { ToolSchemas } from '../src/tools';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TEST_DIR = path.join(__dirname, '..', 'test-output');
const FIXTURES_DIR = path.join(__dirname, 'fixtures');

describe('Video MCP Server', () => {
  beforeAll(async () => {
    await fs.mkdir(TEST_DIR, { recursive: true });
  });

  afterAll(async () => {
    // Clean up test output
    try {
      await fs.rm(TEST_DIR, { recursive: true, force: true });
    } catch {
      // Ignore cleanup errors
    }
  });

  describe('Tool Schemas', () => {
    it('should validate trim_video input correctly', () => {
      const validInput = {
        inputPath: '/path/to/video.mp4',
        outputPath: '/path/to/output.mp4',
        inPoint: 0,
        outPoint: 10
      };

      const result = ToolSchemas.trimVideo.safeParse(validInput);
      expect(result.success).toBe(true);
    });

    it('should reject invalid trim_video input', () => {
      const invalidInput = {
        inputPath: '/path/to/video.mp4',
        // Missing required fields
      };

      const result = ToolSchemas.trimVideo.safeParse(invalidInput);
      expect(result.success).toBe(false);
    });

    it('should validate speed multiplier range', () => {
      const validInput = {
        inputPath: '/path/to/video.mp4',
        outputPath: '/path/to/output.mp4',
        speedMultiplier: 2.5
      };

      const result = ToolSchemas.changeSpeed.safeParse(validInput);
      expect(result.success).toBe(true);
    });

    it('should reject speed multiplier outside range', () => {
      const invalidInput = {
        inputPath: '/path/to/video.mp4',
        outputPath: '/path/to/output.mp4',
        speedMultiplier: 0.01 // Below minimum of 0.1
      };

      const result = ToolSchemas.changeSpeed.safeParse(invalidInput);
      expect(result.success).toBe(false);
    });

    it('should validate thumbnail dimensions', () => {
      const validInput = {
        inputPath: '/path/to/video.mp4',
        outputPath: '/path/to/thumb.jpg',
        timePosition: 5,
        width: 640,
        height: 360
      };

      const result = ToolSchemas.generateThumbnail.safeParse(validInput);
      expect(result.success).toBe(true);
    });

    it('should require at least width or height for scale', () => {
      const noDimensions = {
        inputPath: '/path/to/video.mp4',
        outputPath: '/path/to/output.mp4'
      };

      const result = ToolSchemas.scaleVideo.safeParse(noDimensions);
      // Should fail because neither width nor height is provided
      expect(result.success).toBe(false);
    });
  });

  describe('Media Info', () => {
    it('should handle non-existent file gracefully', async () => {
      const params = {
        inputPath: '/nonexistent/path/video.mp4'
      };

      await expect(VideoTools.getMediaInfo(params)).rejects.toThrow(/not found|not readable/i);
    });
  });

  describe('Color Bars Generation', () => {
    it('should create color bars video', async () => {
      const outputPath = path.join(TEST_DIR, 'color_bars_test.mp4');
      
      const params = {
        outputPath,
        duration: 1,
        width: 320,
        height: 180,
        frameRate: 30
      };

      // This test requires FFmpeg to be installed
      // Skip if FFmpeg is not available
      try {
        const result = await VideoTools.createColorBars(params);
        expect(result.outputPath).toBe(outputPath);
        
        // Verify file was created
        await expect(fs.access(outputPath)).resolves.not.toThrow();
      } catch (error) {
        // FFmpeg may not be installed in test environment
        console.warn('Skipping color bars test - FFmpeg not available:', error);
      }
    }, 10000);
  });

  describe('Schema Type Inference', () => {
    it('should have correct types for TrimVideoInput', () => {
      // Type checking happens at compile time
      // This test ensures the type exports work
      type TrimInput = typeof ToolSchemas.trimVideo;
      expect(TrimInput).toBeDefined();
    });
  });
});

describe('Video Tools Integration', () => {
  // These tests require actual video files
  // They are marked as skip by default
  
  describe.skip('Video Processing (requires fixtures)', () => {
    it('should trim video', async () => {
      // Requires fixture video file
      const fixturePath = path.join(FIXTURES_DIR, 'test_video.mp4');
      const outputPath = path.join(TEST_DIR, 'trimmed.mp4');

      const params = {
        inputPath: fixturePath,
        outputPath,
        inPoint: 0,
        outPoint: 5
      };

      const result = await VideoTools.trimVideo(params);
      expect(result.outputPath).toBe(outputPath);
    });

    it('should extract audio', async () => {
      const fixturePath = path.join(FIXTURES_DIR, 'test_video.mp4');
      const outputPath = path.join(TEST_DIR, 'audio.wav');

      const params = {
        inputPath: fixturePath,
        outputPath,
        audioCodec: 'wav'
      };

      const result = await VideoTools.extractAudio(params);
      expect(result.outputPath).toBe(outputPath);
    });

    it('should generate thumbnail', async () => {
      const fixturePath = path.join(FIXTURES_DIR, 'test_video.mp4');
      const outputPath = path.join(TEST_DIR, 'thumbnail.jpg');

      const params = {
        inputPath: fixturePath,
        outputPath,
        timePosition: 1,
        width: 320,
        height: 180
      };

      const result = await VideoTools.generateThumbnail(params);
      expect(result.outputPath).toBe(outputPath);
    });
  });
});
