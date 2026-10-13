"""Time-aware One Euro fingertip smoothing for responsive hand control."""

import math

from config import (
    HAND_MAX_POINT_JUMP,
    HAND_SMOOTHING_BETA,
    HAND_SMOOTHING_DERIVATIVE_CUTOFF,
    HAND_SMOOTHING_MIN_CUTOFF,
    HAND_TRACKING_GAP_SECONDS,
)


def _alpha(cutoff, delta_time):
    tau = 1.0 / (2.0 * math.pi * cutoff)
    return 1.0 / (1.0 + tau / delta_time)


class _LowPass:
    def __init__(self):
        self.value = None

    def update(self, value, alpha):
        if self.value is None:
            self.value = value
        else:
            self.value += alpha * (value - self.value)
        return self.value


class _OneEuroAxis:
    def __init__(self, min_cutoff, beta, derivative_cutoff):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.derivative_cutoff = derivative_cutoff
        self.raw_value = None
        self.value_filter = _LowPass()
        self.derivative_filter = _LowPass()

    def update(self, value, delta_time):
        if self.raw_value is None:
            derivative = 0.0
        else:
            derivative = (value - self.raw_value) / delta_time
        self.raw_value = value
        derivative = self.derivative_filter.update(
            derivative,
            _alpha(self.derivative_cutoff, delta_time),
        )
        cutoff = self.min_cutoff + self.beta * abs(derivative)
        return self.value_filter.update(value, _alpha(cutoff, delta_time))


class _OneEuroPoint:
    def __init__(self, point, timestamp):
        self.x_filter = _OneEuroAxis(
            HAND_SMOOTHING_MIN_CUTOFF,
            HAND_SMOOTHING_BETA,
            HAND_SMOOTHING_DERIVATIVE_CUTOFF,
        )
        self.y_filter = _OneEuroAxis(
            HAND_SMOOTHING_MIN_CUTOFF,
            HAND_SMOOTHING_BETA,
            HAND_SMOOTHING_DERIVATIVE_CUTOFF,
        )
        self.timestamp = timestamp
        self.raw_point = point
        self.point = (
            self.x_filter.update(point[0], 1.0 / 30.0),
            self.y_filter.update(point[1], 1.0 / 30.0),
        )

    def update(self, point, timestamp):
        delta_time = timestamp - self.timestamp
        if (
            delta_time <= 0
            or delta_time > HAND_TRACKING_GAP_SECONDS
            or math.dist(point, self.raw_point) > HAND_MAX_POINT_JUMP
        ):
            self.__init__(point, timestamp)
            return self.point, True

        self.raw_point = point
        self.timestamp = timestamp
        self.point = (
            self.x_filter.update(point[0], delta_time),
            self.y_filter.update(point[1], delta_time),
        )
        return self.point, False


class FingertipSmoother:
    """Smooth each hand independently and reset immediately after tracking loss."""

    def __init__(self):
        self.filters = {}
        self.clock = 0.0

    def update(self, hands, delta_time):
        self.clock += max(0.0, delta_time)
        active = set()
        output = []
        for index, hand in enumerate(hands):
            if not hand or len(hand.get("landmarks", [])) <= 8:
                continue
            key = hand.get("tracking_id", hand.get("handedness", index))
            if key in active:
                continue
            active.add(key)
            landmarks = list(hand["landmarks"])
            raw_point = landmarks[8]
            timestamp = hand.get("timestamp_ms")
            timestamp = timestamp / 1000.0 if timestamp is not None else self.clock

            point_filter = self.filters.get(key)
            if point_filter is None:
                point_filter = _OneEuroPoint(raw_point, timestamp)
                self.filters[key] = point_filter
                point = raw_point
            elif timestamp == point_filter.timestamp:
                # The render loop may reuse the latest async inference result.
                point = point_filter.point
            else:
                point, _reset = point_filter.update(raw_point, timestamp)

            landmarks[8] = (round(point[0]), round(point[1]))
            output.append({**hand, "landmarks": landmarks, "tracking_id": key})

        self.filters = {
            key: point_filter
            for key, point_filter in self.filters.items()
            if key in active
        }
        return output
