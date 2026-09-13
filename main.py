"""Fruit Ninja real-time hand-tracking game entry point."""

import os
import sys
from collections import deque

import cv2

from config import (
    CONNECTION_COLOR,
    CONNECTION_THICKNESS,
    DISPLAY_NAME,
    FPS,
    GESTURE_HAND_RADIUS,
    GESTURE_HISTORY_SIZE,
    GESTURE_VELOCITY_THRESHOLD,
    LANDMARK_COLOR,
    LANDMARK_RADIUS,
)
from game.fruit_spawner import FruitSpawner
from game.game_engine import GameEngine
from game.game_manager import GameManager
from game.gesture_detector import GestureDetector
from ui.hud import HUD
from vision.hand_tracker import HandTracker
from vision.smoothing import FingertipSmoother


def main():
    """Run the real-time gameplay loop."""
    print("=" * 60)
    print("Fruit Ninja - Real-Time Hand Tracking")
    print("=" * 60)
    print("\nImplemented gameplay:")
    print("- Camera feed and MediaPipe hand tracking")
    print("- Fruit spawning with gravity physics")
    print("- Velocity-based slicing gestures")
    print("- Fruit and bomb collision handling")
    print("- Lives, score, combo, and game-over state")
    print("- FPS counter and hand-trail visualization")
    print("\nControls:")
    print("  Q or ESC: Quit")
    print("=" * 60)
    print("\nInitializing...\n")

    engine = None
    hand_tracker = None
    hud = None
    spawner = None
    gesture_detector = None
    game_manager = None

    try:
        print("Initializing Game Engine...")
        sys.stdout.flush()
        engine = GameEngine()
        print("[OK] Game engine initialized")
        sys.stdout.flush()

        print("Initializing Hand Tracker...")
        sys.stdout.flush()
        hand_tracker = HandTracker()
        print("[OK] Hand tracker initialized")
        sys.stdout.flush()

        print("Initializing HUD...")
        sys.stdout.flush()
        hud = HUD()
        print("[OK] HUD initialized")
        sys.stdout.flush()

        print("Initializing Fruit Spawner...")
        sys.stdout.flush()
        spawner = FruitSpawner()
        print("[OK] Fruit spawner initialized")
        sys.stdout.flush()

        print("Initializing Gesture Detector...")
        sys.stdout.flush()
        gesture_detector = GestureDetector(GESTURE_HISTORY_SIZE, GESTURE_VELOCITY_THRESHOLD)
        smoother = FingertipSmoother()
        print("[OK] Gesture detector initialized")
        sys.stdout.flush()

        print("Initializing Game Manager...")
        sys.stdout.flush()
        game_manager = GameManager()
        game_manager.set_state(GameManager.STATE_PLAYING)
        print("[OK] Game manager initialized")
        sys.stdout.flush()

        print(f"\n[OK] Starting game loop at {FPS} FPS...")
        print("-" * 60)
        sys.stdout.flush()

        frame_count = 0
        max_frames = int(os.environ.get("MAX_FRAMES", "0"))
        visual_trails = {}

        while True:
            frame = engine.get_camera_frame()
            if frame is None:
                print("Error: Could not read from camera")
                break

            if frame_count == 0:
                print(f"[OK] Camera frame captured: {frame.shape}")
                sys.stdout.flush()

            frame, hands_data = hand_tracker.process_frame(frame)
            hands_data = smoother.update(hands_data, engine.delta_time)

            if frame_count == 0:
                print(f"[OK] Hand detection working (found {len(hands_data)} hands)")
                sys.stdout.flush()

            current_hand_indices = []
            for idx, hand_data in enumerate(hands_data):
                if hand_data is None or hand_data.get("sliced", False):
                    continue
                idx = hand_data.get("tracking_id", idx)
                landmarks = hand_data.get("landmarks", [])
                if len(landmarks) > 8:
                    index_finger = landmarks[8]
                    if idx not in visual_trails:
                        visual_trails[idx] = deque(maxlen=15)
                    visual_trails[idx].append(index_finger)
                    current_hand_indices.append(idx)

            visual_trails = {
                key: trail
                for key, trail in visual_trails.items()
                if key in current_hand_indices
            }

            for trail in visual_trails.values():
                if len(trail) <= 1:
                    continue
                points = [(int(point[0]), int(point[1])) for point in trail]
                for index in range(len(points) - 1):
                    factor = index / len(points)
                    thickness = max(1, int(15 * factor))
                    color = (0, int(255 * factor), 255)
                    cv2.line(frame, points[index], points[index + 1], color, thickness, cv2.LINE_AA)
                    core_thickness = max(1, int(5 * factor))
                    cv2.line(
                        frame,
                        points[index],
                        points[index + 1],
                        (255, 255, 255),
                        core_thickness,
                        cv2.LINE_AA,
                    )

            frame = hand_tracker.draw_landmarks(
                frame,
                hands_data,
                landmark_color=LANDMARK_COLOR,
                landmark_radius=LANDMARK_RADIUS,
                connection_color=CONNECTION_COLOR,
                connection_thickness=CONNECTION_THICKNESS,
            )

            current_state = game_manager.get_state()

            if current_state == GameManager.STATE_MENU:
                hud.set_game_mode("Ready")
                hud.set_score(0)
                hud.set_lives(3)
                hud.set_combo(0)
                hud.set_fruits_sliced(0)
                fruit_count = 0
                bomb_count = 0

            elif current_state == GameManager.STATE_PLAYING:
                spawner.update(engine.delta_time)
                frame = spawner.draw(frame)
                fruit_count = spawner.get_active_fruits_count()
                bomb_count = spawner.get_bomb_count()

                game_manager.update(engine.delta_time)

                for _ in range(spawner.consume_missed_fruits()):
                    if not game_manager.miss_fruit():
                        break

                slices = gesture_detector.update(hands_data, engine.delta_time)
                for slice_data in slices:
                    if game_manager.is_game_over():
                        break
                    hand_pos = slice_data["position"]
                    old_hand_pos = slice_data.get("old_position", hand_pos)

                    nearby_fruits = spawner.get_fruit_intersecting_line(
                        old_hand_pos,
                        hand_pos,
                        radius_padding=GESTURE_HAND_RADIUS,
                    )
                    for fruit in nearby_fruits:
                        spawner.slice_fruit(fruit, slice_data["direction"])
                        game_manager.slice_fruit()

                    nearby_bombs = spawner.get_bomb_intersecting_line(
                        old_hand_pos,
                        hand_pos,
                        radius_padding=GESTURE_HAND_RADIUS,
                    )
                    for bomb in nearby_bombs:
                        spawner.hit_bomb(bomb)
                        if not game_manager.hit_bomb():
                            break

                hud.set_score(game_manager.get_score())
                hud.set_lives(game_manager.get_lives())
                hud.set_combo(game_manager.get_combo())
                hud.set_fruits_sliced(game_manager.fruits_sliced)

                if game_manager.is_game_over():
                    hud.set_game_mode(
                        f"GAME OVER - Final Score: {game_manager.get_score()}"
                    )
                else:
                    hud.set_game_mode(f"Playing: {fruit_count}F {bomb_count}B")

            elif current_state == GameManager.STATE_PAUSED:
                frame = spawner.draw(frame)
                hud.set_game_mode("PAUSED")

            frame = hud.draw(frame)
            frame = engine.draw_fps(frame)
            engine.display_frame(frame, DISPLAY_NAME)
            engine.update_timing()
            frame_count += 1

            if frame_count % 30 == 0:
                print(
                    f"  Frame {frame_count}, FPS: {engine.current_fps}, "
                    f"Score: {game_manager.get_score()}, "
                    f"Lives: {game_manager.get_lives()}, "
                    f"Combo: {game_manager.get_combo()}x"
                )
                sys.stdout.flush()

            engine.maintain_fps()

            if not engine.handle_input():
                break

            if game_manager.is_game_over():
                print("\n[OK] GAME OVER!")
                print(f"  Final Score: {game_manager.get_score()}")
                print(f"  Fruits Sliced: {game_manager.fruits_sliced}")
                print(f"  Bombs Hit: {game_manager.bombs_hit}")
                print(f"  Reason: {game_manager.get_game_over_reason()}")
                break

            if max_frames > 0 and frame_count >= max_frames:
                print(f"Reached max frames limit ({max_frames}), exiting...")
                break

        print("-" * 60)
        print(f"\nTotal frames processed: {frame_count}")
        average_fps = (
            f"{frame_count / engine.clock_time:.1f}"
            if engine.clock_time > 0
            else "N/A"
        )
        print(f"Average FPS: {average_fps}")
        print("\n[OK] Game closed successfully")

    except Exception as exc:
        print(f"\n[ERROR] Error occurred: {exc}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        if hand_tracker:
            hand_tracker.close()
        if engine:
            engine.close()
        if game_manager:
            stats = game_manager.get_stats()
            print("\n" + "=" * 60)
            print("Game Statistics:")
            print(f"Final Score: {stats['score']}")
            print(f"Fruits Sliced: {stats['fruits_sliced']}")
            print(f"Bombs Hit: {stats['bombs_hit']}")
            print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
