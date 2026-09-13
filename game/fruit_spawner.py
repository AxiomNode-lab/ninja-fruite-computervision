"""
Fruit and Bomb Spawner for Fruit Ninja game
Manages fruit and bomb spawning, physics updates, and lifecycle
"""

import random
import cv2
from config import (
    SCREEN_WIDTH, FRUIT_SPAWN_HEIGHT, FRUIT_SPAWN_RATE, GRAVITY,
    FRUIT_RADIUS, FRUIT_TYPES, FRUIT_VEL_MIN_X, FRUIT_VEL_MAX_X,
    FRUIT_VEL_MIN_Y, FRUIT_VEL_MAX_Y
)
from game.fruit import Fruit
from game.bomb import Bomb
from game.slice_effect import SliceEffect


class FruitSpawner:
    """
    Manages fruit and bomb spawning and updates
    
    Attributes:
        fruits: List of active Fruit objects
        bombs: List of active Bomb objects
        spawn_timer: Time accumulator for spawning
        spawn_interval: Time between spawns
        bomb_rate: Probability of spawning bomb instead of fruit (0.0-1.0)
    """
    
    def __init__(self, spawn_rate=FRUIT_SPAWN_RATE, bomb_rate=0.15):
        """
        Initialize spawner
        
        Args:
            spawn_rate: Fruits/bombs per second to spawn
            bomb_rate: Probability of spawning bomb (0.0-1.0)
        """
        self.effects = []
        self.missed_fruits = 0
        self.fruits = []
        self.bombs = []
        self.spawn_timer = 0.0
        self.spawn_interval = 1.0 / spawn_rate if spawn_rate > 0 else 0.5
        self.bomb_rate = bomb_rate
        
    def update(self, delta_time):
        """
        Update all objects and spawn new ones
        
        Args:
            delta_time: Time since last frame in seconds
        """
        # Accumulate spawn timer
        self.spawn_timer += delta_time
        
        # Spawn objects when timer reaches interval
        if self.spawn_timer >= self.spawn_interval:
            self._spawn_object()
            self.spawn_timer = 0.0
        
        # Update existing fruits and bombs
        for fruit in self.fruits:
            fruit.update(delta_time)
        
        for bomb in self.bombs:
            bomb.update(delta_time, GRAVITY)
        
        self.missed_fruits += sum(not f.sliced and f.is_off_screen() for f in self.fruits)
        self.fruits = [f for f in self.fruits if not f.sliced and not f.is_off_screen()]
        self.bombs = [b for b in self.bombs if not b.hit and not b.is_off_screen()]
        for effect in self.effects:
            effect.update(delta_time)
        self.effects = [effect for effect in self.effects if effect.age < 1.0]
    
    def _spawn_object(self):
        """Spawn either a fruit or bomb"""
        # Random horizontal position
        spawn_x = random.randint(FRUIT_RADIUS, SCREEN_WIDTH - FRUIT_RADIUS)
        spawn_y = FRUIT_SPAWN_HEIGHT
        
        # Random velocity
        vx = random.uniform(FRUIT_VEL_MIN_X, FRUIT_VEL_MAX_X)
        vy = random.uniform(FRUIT_VEL_MIN_Y, FRUIT_VEL_MAX_Y)
        
        # Decide fruit or bomb
        if random.random() < self.bomb_rate:
            # Spawn bomb
            bomb = Bomb(spawn_x, spawn_y, vx, vy, radius=FRUIT_RADIUS)
            self.bombs.append(bomb)
        else:
            # Spawn fruit
            fruit_type = random.choice(FRUIT_TYPES)
            fruit = Fruit(spawn_x, spawn_y, vx, vy, fruit_type=fruit_type)
            self.fruits.append(fruit)
    
    def draw(self, frame):
        """
        Draw all objects on frame
        
        Args:
            frame: OpenCV frame to draw on
            
        Returns:
            Modified frame
        """
        for effect in self.effects:
            effect.draw(frame)

        # Draw fruits
        for fruit in self.fruits:
            fruit.draw(frame)
        
        # Draw bombs
        for bomb in self.bombs:
            bomb.draw(frame)
        
        return frame
    
    def get_fruits(self):
        """Get list of active fruits"""
        return self.fruits
    
    def get_bombs(self):
        """Get list of active bombs"""
        return self.bombs
    
    def get_all_objects(self):
        """Get all fruits and bombs"""
        return self.fruits + self.bombs
    
    def get_active_fruits_count(self):
        """Get number of unsliced fruits on screen"""
        return sum(1 for f in self.fruits if not f.sliced)
    
    def get_bomb_count(self):
        """Get number of unhit bombs on screen"""
        return sum(1 for b in self.bombs if not b.hit)
    
    def get_fruit_at_position(self, x, y, radius=10):
        """
        Find fruit near a position
        
        Args:
            x, y: Position to check
            radius: Search radius
            
        Returns:
            List of fruits within radius
        """
        nearby = []
        for fruit in self.fruits:
            dist = ((fruit.x - x) ** 2 + (fruit.y - y) ** 2) ** 0.5
            if dist <= (fruit.radius + radius) and not fruit.sliced:
                nearby.append(fruit)
        return nearby
    
    def get_fruit_intersecting_line(self, p1, p2, radius_padding=10):
        """
        Find fruit intersecting a line segment between p1 and p2
        
        Args:
            p1, p2: (x, y) coordinates of line segment
            radius_padding: Extra radius to account for hand size
            
        Returns:
            List of fruits intersecting the segment
        """
        nearby = []
        for fruit in self.fruits:
            if fruit.sliced:
                continue
            
            fx, fy = fruit.x, fruit.y
            r = fruit.radius + radius_padding
            
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            length_sq = dx*dx + dy*dy
            
            if length_sq == 0:
                dist = ((fx - p1[0])**2 + (fy - p1[1])**2)**0.5
            else:
                t = ((fx - p1[0]) * dx + (fy - p1[1]) * dy) / length_sq
                t = max(0, min(1, t))
                proj_x = p1[0] + t * dx
                proj_y = p1[1] + t * dy
                dist = ((fx - proj_x)**2 + (fy - proj_y)**2)**0.5
                
            if dist <= r:
                nearby.append(fruit)
        return nearby
    
    def get_bomb_at_position(self, x, y, radius=10):
        """
        Find bomb near a position
        
        Args:
            x, y: Position to check
            radius: Search radius
            
        Returns:
            List of bombs within radius
        """
        nearby = []
        for bomb in self.bombs:
            dist = ((bomb.x - x) ** 2 + (bomb.y - y) ** 2) ** 0.5
            if dist <= (bomb.radius + radius) and not bomb.hit:
                nearby.append(bomb)
        return nearby

    def get_bomb_intersecting_line(self, p1, p2, radius_padding=10):
        """
        Find bomb intersecting a line segment between p1 and p2
        """
        nearby = []
        for bomb in self.bombs:
            if bomb.hit:
                continue
            
            bx, by = bomb.x, bomb.y
            r = bomb.radius + radius_padding
            
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            length_sq = dx*dx + dy*dy
            
            if length_sq == 0:
                dist = ((bx - p1[0])**2 + (by - p1[1])**2)**0.5
            else:
                t = ((bx - p1[0]) * dx + (by - p1[1]) * dy) / length_sq
                t = max(0, min(1, t))
                proj_x = p1[0] + t * dx
                proj_y = p1[1] + t * dy
                dist = ((bx - proj_x)**2 + (by - proj_y)**2)**0.5
                
            if dist <= r:
                nearby.append(bomb)
        return nearby
    
    def slice_fruit(self, fruit, direction=(1, 0)):
        """Slice once and retain only the short-lived visual effect."""
        if not fruit.sliced:
            self.effects.append(SliceEffect(fruit, direction))
            fruit.slice()

    def consume_missed_fruits(self):
        count, self.missed_fruits = self.missed_fruits, 0
        return count
    
    def hit_bomb(self, bomb):
        """Mark a bomb as hit"""
        bomb.mark_hit()
    
    def clear(self):
        """Remove all objects"""
        self.effects.clear()
        self.missed_fruits = 0
        self.fruits.clear()
        self.bombs.clear()
        self.spawn_timer = 0.0
    
    def __repr__(self):
        """String representation for debugging"""
        fruits_active = self.get_active_fruits_count()
        bombs_active = self.get_bomb_count()
        return f"Spawner({fruits_active} fruits/{len(self.fruits)} total, {bombs_active} bombs/{len(self.bombs)} total)"
