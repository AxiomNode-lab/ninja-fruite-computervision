"""Fruit physics, rendering, and lifecycle for the Fruit Ninja game."""

import numpy as np

from config import FRUIT_RADIUS, GRAVITY, SCREEN_HEIGHT, SCREEN_WIDTH


class Fruit:
    """Represent one fruit and its physics/rendering state."""

    TYPES = [
        "apple",
        "orange",
        "watermelon",
        "banana",
        "peach",
        "grape",
        "strawberry",
        "lemon",
        "mango",
        "pineapple",
    ]
    def __init__(self, x, y, vx, vy, fruit_type="apple", radius=FRUIT_RADIUS):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.fruit_type = fruit_type
        self.radius = radius
        self.sliced = False
        self.creation_time = 0.0

    def update(self, delta_time):
        if self.sliced:
            return

        self.vy += GRAVITY * delta_time
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time

    def draw(self, frame):
        if not self.sliced:
            from game.fruit_art import composite, fruit_sprite
            composite(frame, fruit_sprite(self.fruit_type, self.radius), self.x, self.y)
        return frame

    def is_off_screen(self):
        if self.y > SCREEN_HEIGHT + self.radius and self.vy > 0:
            return True
        if self.x < -self.radius or self.x > SCREEN_WIDTH + self.radius:
            return True
        return False

    def slice(self):
        self.sliced = True

    def get_position(self):
        return (self.x, self.y)

    def get_bounds(self):
        return (
            self.x - self.radius,
            self.y - self.radius,
            self.x + self.radius,
            self.y + self.radius,
        )

    def is_point_inside(self, px, py):
        distance = np.sqrt((px - self.x) ** 2 + (py - self.y) ** 2)
        return distance <= self.radius

    def __repr__(self):
        sliced_str = " (sliced)" if self.sliced else ""
        return (
            f"Fruit({self.fruit_type} at ({self.x:.0f},{self.y:.0f}), "
            f"v=({self.vx:.0f},{self.vy:.0f}){sliced_str})"
        )
