"""MediaPipe hand-landmark tracking for the Fruit Ninja game."""

import os
import threading
import time

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    RunningMode,
)

from config import (
    HAND_INFERENCE_HEIGHT,
    HAND_INFERENCE_WIDTH,
    HAND_RESULT_MAX_AGE_MS,
    MAX_HANDS,
    MIN_HAND_DETECTION_CONFIDENCE,
    MIN_HAND_PRESENCE_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
)


class HandTracker:
    """Manage MediaPipe hand detection and landmark extraction."""

    def __init__(self):
        self.frame_count = 0
        self.last_timestamp_ms = -1
        self.landmarker = None
        self._result_lock = threading.Lock()
        self._latest_hands = []
        self._latest_result_timestamp_ms = -1
        self._closed = False

        model_path = "hand_landmarker.task"
        try:
            if not os.path.exists(model_path):
                mediapipe_path = os.path.dirname(mp.__file__)
                model_path = os.path.join(
                    mediapipe_path,
                    "tasks",
                    "hand_landmarker.task",
                )

            if os.path.exists(model_path):
                base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
                options = HandLandmarkerOptions(
                    base_options=base_options,
                    running_mode=RunningMode.LIVE_STREAM,
                    num_hands=MAX_HANDS,
                    min_hand_detection_confidence=MIN_HAND_DETECTION_CONFIDENCE,
                    min_hand_presence_confidence=MIN_HAND_PRESENCE_CONFIDENCE,
                    min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
                    result_callback=self._on_result,
                )
                self.landmarker = HandLandmarker.create_from_options(options)
                print("[OK] HandLandmarker initialized successfully")
            else:
                print("[WARNING] Hand landmark model not found; tracking disabled")
        except Exception as exc:
            print(f"[ERROR] Failed to initialize HandLandmarker: {exc}")

    def process_frame(
        self,
        frame: np.ndarray,
        timestamp_ms: int | None = None,
    ) -> tuple[np.ndarray, list[dict]]:
        hands_data = []

        if self.landmarker is None:
            self.frame_count += 1
            return frame, hands_data

        try:
            if timestamp_ms is None:
                timestamp_ms = int(time.monotonic() * 1000)
            timestamp_ms = max(timestamp_ms, self.last_timestamp_ms + 1)
            self.last_timestamp_ms = timestamp_ms

            inference_frame = frame
            if frame.shape[1] != HAND_INFERENCE_WIDTH or frame.shape[0] != HAND_INFERENCE_HEIGHT:
                inference_frame = cv2.resize(
                    frame,
                    (HAND_INFERENCE_WIDTH, HAND_INFERENCE_HEIGHT),
                    interpolation=cv2.INTER_AREA,
                )
            rgb_frame = cv2.cvtColor(inference_frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            # LIVE_STREAM is non-blocking and internally drops new frames while
            # inference is busy, preventing an ever-growing latency queue.
            self.landmarker.detect_async(mp_image, timestamp_ms)

            with self._result_lock:
                result_timestamp_ms = self._latest_result_timestamp_ms
                latest_hands = list(self._latest_hands)

            result_age_ms = timestamp_ms - result_timestamp_ms
            if 0 <= result_age_ms <= HAND_RESULT_MAX_AGE_MS:
                for hand in latest_hands:
                    hands_data.append(
                        {
                            **hand,
                            "landmarks": self._extract_landmarks(
                                hand["normalized_landmarks"],
                                frame,
                            ),
                            "timestamp_ms": result_timestamp_ms,
                            "result_age_ms": result_age_ms,
                        }
                    )

            self.frame_count += 1
        except Exception as exc:
            print(f"Error processing frame: {exc}")
            self.frame_count += 1

        return frame, hands_data

    def _on_result(self, results, _output_image, timestamp_ms):
        """Store only the newest normalized result from MediaPipe's worker."""
        hands = []
        if results.hand_landmarks:
            for hand_idx, hand_landmarks in enumerate(results.hand_landmarks):
                handedness_list = (
                    results.handedness[hand_idx] if results.handedness else None
                )
                handedness = (
                    handedness_list[0]
                    if handedness_list and len(handedness_list) > 0
                    else None
                )
                hands.append(
                    {
                        "normalized_landmarks": [
                            (landmark.x, landmark.y) for landmark in hand_landmarks
                        ],
                        "handedness": (
                            handedness.category_name if handedness else "Unknown"
                        ),
                        "confidence": handedness.score if handedness else 0.0,
                    }
                )

        with self._result_lock:
            if self._closed or timestamp_ms < self._latest_result_timestamp_ms:
                return
            self._latest_hands = hands
            self._latest_result_timestamp_ms = timestamp_ms

    def _extract_landmarks(
        self,
        normalized_landmarks,
        frame: np.ndarray,
    ) -> list[tuple[int, int]]:
        height, width, _ = frame.shape
        return [
            (
                min(width - 1, max(0, round(x * width))),
                min(height - 1, max(0, round(y * height))),
            )
            for x, y in normalized_landmarks
        ]

    def draw_landmarks(
        self,
        frame: np.ndarray,
        hands_data: list[dict],
        landmark_color: tuple[int, int, int] = (0, 255, 0),
        landmark_radius: int = 5,
        connection_color: tuple[int, int, int] = (0, 255, 255),
        connection_thickness: int = 2,
    ) -> np.ndarray:
        connections = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 4),
            (0, 5),
            (5, 6),
            (6, 7),
            (7, 8),
            (0, 9),
            (9, 10),
            (10, 11),
            (11, 12),
            (0, 13),
            (13, 14),
            (14, 15),
            (15, 16),
            (0, 17),
            (17, 18),
            (18, 19),
            (19, 20),
            (5, 9),
            (9, 13),
            (13, 17),
        ]

        for hand_info in hands_data:
            landmarks = hand_info["landmarks"]
            for start, end in connections:
                if start < len(landmarks) and end < len(landmarks):
                    cv2.line(
                        frame,
                        landmarks[start],
                        landmarks[end],
                        connection_color,
                        connection_thickness,
                    )

            for x, y in landmarks:
                cv2.circle(frame, (x, y), landmark_radius, landmark_color, -1)

        return frame

    def get_index_finger_tip(self, hand_info: dict) -> tuple[int, int] | None:
        landmarks = hand_info["landmarks"]
        if len(landmarks) > 8:
            return landmarks[8]
        return None

    def close(self):
        if self.landmarker:
            with self._result_lock:
                self._closed = True
                self._latest_hands = []
            self.landmarker.close()
            self.landmarker = None
