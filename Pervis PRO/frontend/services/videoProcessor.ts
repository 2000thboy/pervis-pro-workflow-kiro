
// Utility to process video blobs in the browser

export const videoProcessor = {
  
  /**
   * Generates a thumbnail from a video Blob at a specific time (default 1s).
   * Returns a Blob of the image (JPEG).
   */
  generateThumbnail: async (videoBlob: Blob, seekTime: number = 1.0): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const video = document.createElement('video');
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      // Safety timeout
      const timeout = setTimeout(() => {
        cleanup();
        reject(new Error("Thumbnail generation timed out"));
      }, 5000);

      const cleanup = () => {
        clearTimeout(timeout);
        URL.revokeObjectURL(video.src);
        video.remove();
        canvas.remove();
      };

      video.autoplay = false;
      video.muted = true;
      video.src = URL.createObjectURL(videoBlob);
      video.crossOrigin = "anonymous"; // Important if using remote URLs later

      // 1. Load Metadata
      video.onloadedmetadata = () => {
        video.currentTime = seekTime;
      };

      // 2. Seeked -> Draw
      video.onseeked = () => {
        // Set canvas dimensions (downscale for thumbnail if needed, e.g., max 640px width)
        const maxWidth = 640;
        const scale = Math.min(1, maxWidth / video.videoWidth);
        
        canvas.width = video.videoWidth * scale;
        canvas.height = video.videoHeight * scale;
        
        ctx?.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        canvas.toBlob((blob) => {
          cleanup();
          if (blob) resolve(blob);
          else reject(new Error("Canvas to Blob failed"));
        }, 'image/jpeg', 0.8);
      };

      video.onerror = () => {
        cleanup();
        reject(new Error("Video load failed"));
      };
    });
  }
};
