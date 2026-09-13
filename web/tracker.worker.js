const VERSION = '0.10.22-rc.20250304';
let tracker;
self.onmessage = async ({ data }) => {
  try {
    if (data.type === 'init') {
      const { HandLandmarker, FilesetResolver } = await import(`https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${VERSION}/vision_bundle.mjs`);
      const files = await FilesetResolver.forVisionTasks(`https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${VERSION}/wasm`);
      tracker = await HandLandmarker.createFromOptions(files, {
        baseOptions: { modelAssetPath: new URL('../hand_landmarker.task', self.location.href).href, delegate: 'CPU' },
        runningMode: 'VIDEO', numHands: 2, minHandDetectionConfidence: .6,
        minHandPresenceConfidence: .6, minTrackingConfidence: .6,
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
