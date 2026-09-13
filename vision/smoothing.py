"""Time-aware fingertip smoothing without adding lag to fast swipes."""

import math


class FingertipSmoother:
    def __init__(self):
        self.points = {}

    def update(self, hands, delta_time):
        active = set()
        output = []
        for index, hand in enumerate(hands):
            if not hand or len(hand.get("landmarks", [])) <= 8:
                continue
            key = hand.get("handedness", index)
            if key in active:
                continue
            active.add(key)
            landmarks = list(hand["landmarks"])
            x, y = landmarks[8]
            previous = self.points.get(key)
            if previous and 0 < delta_time < 0.15:
                distance = math.hypot(x - previous[0], y - previous[1])
                if distance < 330:
                    cutoff = 2.4 + 0.018 * distance / delta_time
                    alpha = 1 - math.exp(-2 * math.pi * cutoff * delta_time)
                    x = previous[0] + alpha * (x - previous[0])
                    y = previous[1] + alpha * (y - previous[1])
            self.points[key] = (x, y)
            landmarks[8] = (round(x), round(y))
            output.append({**hand, "landmarks": landmarks, "tracking_id": key})
        self.points = {key: point for key, point in self.points.items() if key in active}
        return output
