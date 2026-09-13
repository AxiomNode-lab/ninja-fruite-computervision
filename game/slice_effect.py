"""Two separating fruit halves and short-lived juice particles."""

import math
import random

import cv2
import numpy as np

from config import FRUIT_COLORS, GRAVITY
from game.fruit_art import composite, fruit_sprite


class SliceEffect:
    def __init__(self, fruit, direction=(1, 0)):
        self.age = 0
        angle = math.atan2(direction[1], direction[0])
        nx, ny = -math.sin(angle), math.cos(angle)
        sprite = fruit_sprite(fruit.fruit_type, fruit.radius)
        yy, xx = np.indices(sprite.shape[:2])
        distance = (xx - sprite.shape[1] / 2) * nx + (yy - sprite.shape[0] / 2) * ny
        self.halves = []
        for side in (-1, 1):
            half = sprite.copy()
            mask = distance * side >= 0 if side == 1 else distance * side > 0
            half[~mask, 3] = 0
            interior = mask & (np.abs(distance) < 4) & (half[:, :, 3] > 0)
            half[interior, :3] = (130, 200, 255) if fruit.fruit_type != "watermelon" else (85, 75, 245)
            self.halves.append([half, fruit.x, fruit.y, fruit.vx + nx * side * 140,
                                fruit.vy * .25 + ny * side * 140 - 60, side])
        self.color = FRUIT_COLORS.get(fruit.fruit_type, (0, 180, 255))
        self.drops = []
        for _ in range(22):
            a, speed = random.uniform(0, math.tau), random.uniform(60, 280)
            self.drops.append([fruit.x, fruit.y, math.cos(a) * speed,
                               math.sin(a) * speed - 70, random.randint(2, 6)])

    def update(self, dt):
        self.age += dt
        for half in self.halves:
            half[4] += GRAVITY * dt
            half[1] += half[3] * dt
            half[2] += half[4] * dt
        for drop in self.drops:
            drop[3] += GRAVITY * dt
            drop[0] += drop[2] * dt
            drop[1] += drop[3] * dt

    def draw(self, frame):
        opacity = max(0, 1 - self.age / 1.0)
        for sprite, x, y, _, _, side in self.halves:
            h, w = sprite.shape[:2]
            transform = cv2.getRotationMatrix2D((w / 2, h / 2), self.age * side * 100, 1)
            rotated = cv2.warpAffine(sprite, transform, (w, h))
            composite(frame, rotated, x, y, opacity)
        if self.age < .65:
            overlay = frame.copy()
            for x, y, _, _, r in self.drops:
                cv2.circle(overlay, (int(x), int(y)), r, self.color, -1, cv2.LINE_AA)
            cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)
        return frame
