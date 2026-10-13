# Game Configuration
# ==================

# Screen/Display Settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 30
DISPLAY_NAME = "Fruit Ninja - Hand Tracking"

# Colors (RGB)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_CYAN = (0, 255, 255)
COLOR_MAGENTA = (255, 0, 255)
COLOR_GRAY = (128, 128, 128)

# Hand Tracking Settings
# Keep these thresholds separate: raising presence/tracking too aggressively makes
# a valid hand disappear and forces MediaPipe to run palm detection more often.
MIN_HAND_DETECTION_CONFIDENCE = 0.5
MIN_HAND_PRESENCE_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5
MAX_HANDS = 2
HAND_INFERENCE_WIDTH = 640
HAND_INFERENCE_HEIGHT = 360
HAND_RESULT_MAX_AGE_MS = 150

# Backwards-compatible aliases for code importing the old names.
HAND_DETECTION_CONFIDENCE = MIN_HAND_DETECTION_CONFIDENCE
HAND_TRACKING_CONFIDENCE = MIN_TRACKING_CONFIDENCE

# One Euro fingertip filter. It damps small stationary jitter while allowing a
# fast swipe to catch up quickly.
HAND_SMOOTHING_MIN_CUTOFF = 1.7
HAND_SMOOTHING_BETA = 0.22
HAND_SMOOTHING_DERIVATIVE_CUTOFF = 1.0
HAND_TRACKING_GAP_SECONDS = 0.15
HAND_MAX_POINT_JUMP = 330

# Landmark Colors
LANDMARK_COLOR = COLOR_GREEN
LANDMARK_RADIUS = 5
CONNECTION_COLOR = COLOR_CYAN
CONNECTION_THICKNESS = 2

# Game Physics
GRAVITY = 250  # pixels/second^2 (delta_time aware)
FRUIT_SPAWN_RATE = 2  # fruits per second
FRUIT_RADIUS = 40  # pixels
FRUIT_SPAWN_HEIGHT = 780  # spawn below screen

# Fruit velocity ranges (pixels/second)
FRUIT_VEL_MIN_X = -100
FRUIT_VEL_MAX_X = 100
FRUIT_VEL_MIN_Y = -650
FRUIT_VEL_MAX_Y = -500

# Fruit types and colors
FRUIT_TYPES = [
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
FRUIT_COLORS = {
    "apple": (0, 0, 255),
    "orange": (0, 165, 255),
    "watermelon": (0, 100, 0),
    "banana": (0, 255, 255),
    "peach": (0, 100, 200),
    "grape": (128, 0, 128),
    "strawberry": (0, 0, 200),
    "lemon": (0, 255, 255),
    "mango": (0, 100, 255),
    "pineapple": (0, 165, 255),
}

# Gesture Detection
GESTURE_VELOCITY_THRESHOLD = 150  # pixels/second
GESTURE_HISTORY_SIZE = 5
GESTURE_HAND_RADIUS = 60

# Scoring
POINTS_PER_FRUIT = 10
POINTS_PER_COMBO = 5
PENALTY_BOMB = -50
INITIAL_LIVES = 3
