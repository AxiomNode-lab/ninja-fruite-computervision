"""
Game Engine Module
Core game loop and frame management
"""

import cv2
import time
from typing import Optional, List
import numpy as np
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, DISPLAY_NAME


class GameEngine:
    """Main game engine handling game loop and FPS"""
    
    def __init__(self, width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT, 
                 target_fps: int = FPS):
        """
        Initialize game engine
        
        Args:
            width: Screen width in pixels
            height: Screen height in pixels
            target_fps: Target frames per second
        """
        self.width = width
        self.height = height
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps
        
        # Timing variables
        self.clock_time = 0
        self.last_frame_time = time.time()
        self.delta_time = 0
        self.frame_count = 0
        self.fps_clock = time.time()
        self.current_fps = 0
        
        # Camera setup
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
        
    def get_camera_frame(self) -> Optional[np.ndarray]:
        """
        Capture frame from camera
        
        Returns:
            Frame array or None if capture failed
        """
        ret, frame = self.cap.read()
        
        if not ret:
            return None
        
        # Match the browser's object-fit: cover behavior without stretching the
        # hand when a 4:3 camera feeds the 16:9 game window.
        source_height, source_width = frame.shape[:2]
        source_ratio = source_width / source_height
        target_ratio = self.width / self.height
        if source_ratio > target_ratio:
            crop_width = round(source_height * target_ratio)
            offset = (source_width - crop_width) // 2
            frame = frame[:, offset : offset + crop_width]
        elif source_ratio < target_ratio:
            crop_height = round(source_width / target_ratio)
            offset = (source_height - crop_height) // 2
            frame = frame[offset : offset + crop_height, :]
        frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_AREA)
        frame = cv2.flip(frame, 1)
        
        return frame
    
    def update_timing(self):
        """Update frame timing and calculate delta time"""
        current_time = time.time()
        self.delta_time = current_time - self.last_frame_time
        self.last_frame_time = current_time
        self.clock_time += self.delta_time
        self.frame_count += 1
        
        # Update FPS counter every second
        if current_time - self.fps_clock >= 1.0:
            self.current_fps = self.frame_count
            self.frame_count = 0
            self.fps_clock = current_time
    
    def maintain_fps(self):
        """Sleep to maintain target FPS"""
        elapsed = time.time() - self.last_frame_time
        sleep_time = self.frame_time - elapsed
        
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    def draw_fps(self, frame: np.ndarray, position: tuple = (10, 30),
                 font_scale: float = 1.0, color: tuple = (0, 255, 0)) -> np.ndarray:
        """
        Draw FPS counter on frame
        
        Args:
            frame: Frame to draw on
            position: (x, y) position for text
            font_scale: Font size scale
            color: RGB color of text
            
        Returns:
            Frame with FPS drawn
        """
        fps_text = f"FPS: {self.current_fps}"
        cv2.putText(frame, fps_text, position, cv2.FONT_HERSHEY_SIMPLEX, 
                   font_scale, color, 2)
        return frame
    
    def display_frame(self, frame: np.ndarray, window_name: str = DISPLAY_NAME):
        """
        Display frame in OpenCV window
        
        Args:
            frame: Frame to display
            window_name: Name of the display window
        """
        cv2.imshow(window_name, frame)
    
    def handle_input(self) -> bool:
        """
        Handle keyboard input
        
        Returns:
            True if application should continue, False if user wants to quit
        """
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q') or key == 27:  # 'q' or ESC
            return False
        
        return True
    
    def close(self):
        """Release resources"""
        self.cap.release()
        cv2.destroyAllWindows()
