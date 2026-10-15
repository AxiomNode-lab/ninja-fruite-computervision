let tracker;
self.onmessage = async ({ data }) => {
  try {
    if (data.type === 'init') {
      self.postMessage({ type: 'status', message: 'Loading hand-tracking engine…' });
      const bundleUrl = new URL('../vendor/mediapipe/vision_bundle.mjs', self.location.href).href;
      const wasmUrl = new URL('../vendor/mediapipe/wasm', self.location.href).href;
      const { HandLandmarker, FilesetResolver } = await import(bundleUrl);
      self.postMessage({ type: 'status', message: 'Starting hand-tracking engine…' });
      const files = await FilesetResolver.forVisionTasks(wasmUrl);
      self.postMessage({ type: 'status', message: 'Loading hand model…' });
      tracker = await HandLandmarker.createFromOptions(files, {
        baseOptions: { modelAssetPath: new URL('../hand_landmarker.task', self.location.href).href, delegate: 'CPU' },
        runningMode: 'VIDEO', numHands: 2, minHandDetectionConfidence: .5,
        minHandPresenceConfidence: .5, minTrackingConfidence: .5,
      });
      self.postMessage({ type: 'ready' });
    } else if (data.type === 'frame') {
      try {
        const result = tracker.detectForVideo(data.bitmap, data.time);
        self.postMessage({ type: 'hands', landmarks: result.landmarks, handedness: result.handedness, time: data.time });
      } finally { data.bitmap.close(); }
    }
  } catch (error) { self.postMessage({ type: 'error', message: error.message }); }
};
