import unittest

import numpy as np

from config import SCREEN_HEIGHT
from game.fruit import Fruit
from game.fruit_spawner import FruitSpawner
from game.gesture_detector import GestureDetector
from vision.smoothing import FingertipSmoother


def hand(x, name="Left"):
    points = [(0, 0)] * 21
    points[8] = (x, 100)
    return {"landmarks": points, "handedness": name}


class PolishTests(unittest.TestCase):
    def test_misses_survive_cleanup_and_are_consumed_once(self):
        spawner = FruitSpawner()
        spawner.fruits = [Fruit(100, SCREEN_HEIGHT + 100, 0, 20)]
        spawner.update(.01)
        self.assertEqual(spawner.fruits, [])
        self.assertEqual(spawner.consume_missed_fruits(), 1)
        self.assertEqual(spawner.consume_missed_fruits(), 0)

    def test_slice_effect_survives_fruit_and_expires(self):
        spawner = FruitSpawner(spawn_rate=.001)
        fruit = Fruit(100, 100, 0, 0)
        spawner.fruits = [fruit]
        spawner.slice_fruit(fruit)
        spawner.slice_fruit(fruit)
        self.assertEqual(len(spawner.effects), 1)
        spawner.update(.1)
        self.assertEqual(spawner.fruits, [])
        frame = np.zeros((250, 250, 3), dtype=np.uint8)
        spawner.draw(frame)
        self.assertGreater(frame.sum(), 0)
        spawner.update(1)
        self.assertEqual(spawner.effects, [])

    def test_fruit_draws_partially_offscreen(self):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        Fruit(0, 50, 0, 0).draw(frame)
        self.assertGreater(frame.sum(), 0)

    def test_smoothing_and_reacquisition(self):
        smoother = FingertipSmoother()
        smoother.update([hand(100)], .033)
        self.assertLess(smoother.update([hand(104)], .033)[0]["landmarks"][8][0], 104)
        smoother.update([], .033)
        self.assertEqual(smoother.update([hand(300)], .033)[0]["landmarks"][8][0], 300)

    def test_hand_order_change_does_not_create_slice(self):
        smoother = FingertipSmoother()
        detector = GestureDetector(velocity_threshold=100)
        detector.update(smoother.update([hand(100), hand(600, "Right")], .033), .033)
        result = detector.update(smoother.update([hand(600, "Right"), hand(100)], .033), .033)
        self.assertEqual(result, [])

    def test_invalid_hand_clears_history(self):
        detector = GestureDetector()
        detector.update([hand(100)], .033)
        detector.update([None], .033)
        self.assertEqual(detector.hand_histories, {})
