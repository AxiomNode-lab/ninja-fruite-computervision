"""Velocity-based slicing gesture detection for the Fruit Ninja game."""

from collections import deque

import numpy as np


class GestureDetector:
    """Track index-finger motion and detect fast slicing gestures."""

    def __init__(self, history_size=5, velocity_threshold=500):
        self.history_size = history_size
        self.velocity_threshold = velocity_threshold
        self.hand_histories = {}
        self.last_timestamp = 0.0

    def update(self, hands_data, delta_time):
        slices = []
        self.last_timestamp += delta_time

        detected_indices = set()
        for hand_idx, hand_data in enumerate(hands_data):
            if hand_data is None or hand_data.get("sliced", False):
                continue

            landmarks = hand_data.get("landmarks", [])
            if len(landmarks) <= 8:
                continue

            hand_idx = hand_data.get("tracking_id", hand_idx)
            detected_indices.add(hand_idx)
            if delta_time > 0.15:
                self.hand_histories.pop(hand_idx, None)
            x, y = landmarks[8]
            if hand_idx not in self.hand_histories:
                self.hand_histories[hand_idx] = deque(maxlen=self.history_size)

            history = self.hand_histories[hand_idx]
            history.append((x, y, self.last_timestamp))

            if len(history) >= 2:
                slice_detected = self._check_for_slice(history, hand_idx)
                if slice_detected:
                    slices.append(slice_detected)

        stale_indices = [
            hand_idx
            for hand_idx in self.hand_histories
            if hand_idx not in detected_indices
        ]
        for hand_idx in stale_indices:
            del self.hand_histories[hand_idx]

        return slices

    def _check_for_slice(self, history, hand_idx):
        if len(history) < 2:
            return None

        x1, y1, t1 = history[-2]
        x2, y2, t2 = history[-1]
        delta_time = t2 - t1
        if delta_time <= 0:
            return None

        dx = x2 - x1
        dy = y2 - y1
        velocity = np.sqrt(dx**2 + dy**2) / delta_time

        if velocity < self.velocity_threshold:
            return None

        return {
            "hand_index": hand_idx,
            "position": (x2, y2),
            "old_position": (x1, y1),
            "velocity": velocity,
            "direction": (dx / delta_time, dy / delta_time),
        }

    def get_hand_position(self, hand_idx):
        history = self.hand_histories.get(hand_idx)
        if not history:
            return None
        x, y, _ = history[-1]
        return (x, y)

    def get_hand_velocity(self, hand_idx):
        history = self.hand_histories.get(hand_idx)
        if history is None or len(history) < 2:
            return None

        x1, y1, t1 = history[0]
        x2, y2, t2 = history[-1]
        delta_time = t2 - t1
        if delta_time <= 0:
            return None

        return ((x2 - x1) / delta_time, (y2 - y1) / delta_time)

    def clear(self):
        self.hand_histories.clear()
        self.last_timestamp = 0.0

    def __repr__(self):
        tracked = len(self.hand_histories)
        return (
            f"GestureDetector(tracking {tracked} hands, "
            f"threshold={self.velocity_threshold}px/s)"
        )
