"""
HANDS OF NOTHING — OpenCV Magic Show System
============================================
Open palm  → 3D particle portal effect (golden floating particles)
Closed fist → Dark vortex / black hole collapse effect
Transition  → Shockwave ripple between states

Run: python main.py
Keys: Q = quit | F = fullscreen | 1/2/3 = force effect | SPACE = freeze frame
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import math
import random


# ──────────────────────────────────────────────
#  CONFIG
# ──────────────────────────────────────────────
WIDTH, HEIGHT = 1280, 720
FULLSCREEN    = False
CAMERA_INDEX  = 0

OPEN_FINGERS_THRESHOLD  = 3   # >= this many fingers up = OPEN
CLOSE_FINGERS_THRESHOLD = 1   # <= this many fingers up = CLOSED
TRANSITION_FRAMES       = 18  # blend frames between states


# ──────────────────────────────────────────────
#  PARTICLE SYSTEM
# ──────────────────────────────────────────────
class Particle:
    def __init__(self, cx, cy, state):
        self.reset(cx, cy, state)

    def reset(self, cx, cy, state):
        self.state = state
        if state == "open":
            angle  = random.uniform(0, 2 * math.pi)
            speed  = random.uniform(1.5, 4.5)
            self.x = cx + random.uniform(-20, 20)
            self.y = cy + random.uniform(-20, 20)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed - random.uniform(0.5, 2.0)
            self.life    = random.uniform(0.6, 1.0)
            self.decay   = random.uniform(0.012, 0.025)
            self.size    = random.uniform(2, 6)
            self.color_h = random.randint(25, 50)   # golden hue range
        else:
            angle  = random.uniform(0, 2 * math.pi)
            radius = random.uniform(80, 220)
            self.x = cx + math.cos(angle) * radius
            self.y = cy + math.sin(angle) * radius
            self.vx = (cx - self.x) * random.uniform(0.03, 0.07)
            self.vy = (cy - self.y) * random.uniform(0.03, 0.07)
            self.life    = random.uniform(0.7, 1.0)
            self.decay   = random.uniform(0.015, 0.030)
            self.size    = random.uniform(1.5, 5)
            self.color_h = random.randint(270, 310)  # purple/violet range

    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.life -= self.decay
        if self.state == "open":
            self.vy  -= 0.05   # float upward
            self.size = max(0.5, self.size - 0.03)
        else:
            self.vx  *= 1.04   # accelerate inward
            self.vy  *= 1.04
            self.size = max(0.5, self.size * 0.985)

    def alive(self):
        return self.life > 0 and 0 < self.x < WIDTH and 0 < self.y < HEIGHT

    def draw(self, canvas):
        alpha  = max(0.0, self.life)
        radius = max(1, int(self.size))
        h = self.color_h / 180.0
        s = 1.0
        v = 1.0
        # HSV → BGR
        hi = int(h * 6) % 6
        f  = h * 6 - int(h * 6)
        p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
        cols = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)]
        r, g, b = cols[hi]
        color = (int(b * 255 * alpha), int(g * 255 * alpha), int(r * 255 * alpha))
        cv2.circle(canvas, (int(self.x), int(self.y)), radius, color, -1, cv2.LINE_AA)


# ──────────────────────────────────────────────
#  SHOCKWAVE
# ──────────────────────────────────────────────
class Shockwave:
    def __init__(self, cx, cy, to_state):
        self.cx       = cx
        self.cy       = cy
        self.radius   = 0
        self.max_r    = max(WIDTH, HEIGHT) * 0.9
        self.speed    = 22
        self.alive    = True
        self.to_state = to_state

    def update(self):
        self.radius += self.speed
        if self.radius > self.max_r:
            self.alive = False

    def draw(self, canvas):
        if not self.alive:
            return
        t     = self.radius / self.max_r
        alpha = max(0.0, 1.0 - t * 1.5)
        thick = max(1, int((1 - t) * 8))
        if self.to_state == "open":
            color = (0, int(180 * alpha), int(255 * alpha))
        else:
            color = (int(200 * alpha), 0, int(180 * alpha))
        if alpha > 0.02:
            cv2.circle(canvas, (int(self.cx), int(self.cy)),
                       int(self.radius), color, thick, cv2.LINE_AA)


# ──────────────────────────────────────────────
#  3D ORBITING RING (open palm effect)
# ──────────────────────────────────────────────
def draw_3d_ring(canvas, cx, cy, t, alpha):
    rings = 3
    for r in range(rings):
        phase  = t * (1.2 + r * 0.3) + r * math.pi / rings
        rx     = 60 + r * 30
        ry     = int(rx * abs(math.sin(phase + 0.3)) * 0.45 + 8)
        pts    = []
        n      = 60
        for i in range(n + 1):
            angle = (i / n) * 2 * math.pi
            px    = int(cx + math.cos(angle) * rx)
            py    = int(cy + math.sin(angle + phase * 0.5) * ry)
            pts.append((px, py))
        bright = int(200 * alpha * (0.6 + 0.4 * abs(math.cos(phase))))
        color  = (0, int(bright * 0.5), bright)
        for i in range(len(pts) - 1):
            cv2.line(canvas, pts[i], pts[i + 1], color, 1, cv2.LINE_AA)


# ──────────────────────────────────────────────
#  VORTEX SPIRAL (closed fist effect)
# ──────────────────────────────────────────────
def draw_vortex(canvas, cx, cy, t, alpha):
    arms = 5
    for arm in range(arms):
        pts = []
        for i in range(120):
            s      = i / 119.0
            angle  = s * 4 * math.pi + (arm / arms) * 2 * math.pi + t * 2.5
            radius = s * 130 * (1 - s * 0.3)
            px     = int(cx + math.cos(angle) * radius)
            py     = int(cy + math.sin(angle) * radius * 0.55)
            pts.append((px, py))
        for i in range(len(pts) - 1):
            fade  = (i / 120.0)
            col_v = int(180 * alpha * fade)
            col_r = int(120 * alpha * fade)
            cv2.line(canvas, pts[i], pts[i + 1],
                     (col_v, 0, col_r), 1, cv2.LINE_AA)


# ──────────────────────────────────────────────
#  GLOW CORE
# ──────────────────────────────────────────────
def draw_glow_core(canvas, cx, cy, state, alpha):
    layers = 6
    for i in range(layers, 0, -1):
        r     = i * 14
        a     = alpha * (1 - i / (layers + 1)) * 0.7
        if state == "open":
            color = (0, int(160 * a), int(255 * a))
        else:
            color = (int(200 * a), 0, int(160 * a))
        cv2.circle(canvas, (cx, cy), r, color, -1, cv2.LINE_AA)


# ──────────────────────────────────────────────
#  FINGER COUNT (MediaPipe)
# ──────────────────────────────────────────────
def count_fingers(hand_landmarks):
    tips  = [4, 8, 12, 16, 20]
    bases = [3, 6, 10, 14, 18]
    count = 0
    # Thumb: x-axis comparison (mirrored camera)
    if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
        count += 1
    # Other fingers: y-axis
    for tip, base in zip(tips[1:], bases[1:]):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[base].y:
            count += 1
    return count


def get_palm_center(hand_landmarks):
    cx = int(np.mean([hand_landmarks.landmark[i].x for i in [0,5,9,13,17]]) * WIDTH)
    cy = int(np.mean([hand_landmarks.landmark[i].y for i in [0,5,9,13,17]]) * HEIGHT)
    return cx, cy


# ──────────────────────────────────────────────
#  OVERLAY TEXT
# ──────────────────────────────────────────────
def draw_hud(canvas, state, fingers, fps, frozen):
    state_txt = "OPEN PALM" if state == "open" else "CLOSED FIST"
    col       = (0, 200, 255) if state == "open" else (200, 0, 180)

    cv2.putText(canvas, state_txt, (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, col, 2, cv2.LINE_AA)
    cv2.putText(canvas, f"Fingers: {fingers}", (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 100, 100), 1, cv2.LINE_AA)
    cv2.putText(canvas, f"FPS: {fps:.0f}", (WIDTH - 100, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 80, 80), 1, cv2.LINE_AA)
    if frozen:
        cv2.putText(canvas, "[ FROZEN ]", (WIDTH // 2 - 60, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (60, 60, 200), 2, cv2.LINE_AA)


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────
def main():
    mp_hands   = mp.solutions.hands
    hands_det  = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.6,
    )

    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    win_name = "HANDS OF NOTHING"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    if FULLSCREEN:
        cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN,
                              cv2.WINDOW_FULLSCREEN)

    # State
    state          = "open"
    prev_state     = "open"
    trans_progress = 1.0          # 0→1 blend
    particles      = []
    shockwaves     = []
    fingers_count  = 5
    cx, cy         = WIDTH // 2, HEIGHT // 2
    t              = 0.0
    frozen         = False
    frozen_canvas  = None
    prev_time      = time.time()
    fps            = 30.0

    PARTICLE_BUDGET = 220

    print("=" * 50)
    print("  HANDS OF NOTHING — Magic Show System")
    print("=" * 50)
    print("  Controls:")
    print("  Q       = Quit")
    print("  F       = Toggle fullscreen")
    print("  SPACE   = Freeze frame")
    print("  1       = Force OPEN effect")
    print("  2       = Force CLOSED effect")
    print("=" * 50)

    while True:
        now  = time.time()
        dt   = now - prev_time
        fps  = 0.9 * fps + 0.1 * (1.0 / max(dt, 0.001))
        prev_time = now
        t   += dt

        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (WIDTH, HEIGHT))

        # ── Hand detection ──────────────────────
        rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands_det.process(rgb)

        detected_fingers = fingers_count
        detected_cx, detected_cy = cx, cy

        if results.multi_hand_landmarks:
            lm = results.multi_hand_landmarks[0]
            detected_fingers   = count_fingers(lm)
            detected_cx, detected_cy = get_palm_center(lm)
            cx, cy = detected_cx, detected_cy

        fingers_count = detected_fingers

        # ── State machine ──────────────────────
        new_state = state
        if fingers_count >= OPEN_FINGERS_THRESHOLD:
            new_state = "open"
        elif fingers_count <= CLOSE_FINGERS_THRESHOLD:
            new_state = "closed"

        if new_state != state:
            prev_state     = state
            state          = new_state
            trans_progress = 0.0
            shockwaves.append(Shockwave(cx, cy, state))
            particles.clear()

        trans_progress = min(1.0, trans_progress + dt * (60 / TRANSITION_FRAMES))
        alpha = trans_progress

        # ── Key state forced by keyboard ───────
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('f'):
            FULLSCREEN_NOW = cv2.getWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(
                win_name, cv2.WND_PROP_FULLSCREEN,
                cv2.WINDOW_NORMAL if FULLSCREEN_NOW else cv2.WINDOW_FULLSCREEN)
        elif key == ord(' '):
            frozen = not frozen
            if frozen:
                frozen_canvas = canvas.copy() if 'canvas' in dir() else None
        elif key == ord('1'):
            state, new_state = "open", "open"
            trans_progress = 1.0
        elif key == ord('2'):
            state, new_state = "closed", "closed"
            trans_progress = 1.0

        if frozen and frozen_canvas is not None:
            cv2.imshow(win_name, frozen_canvas)
            continue

        # ── Build canvas ───────────────────────
        # Dark background (keep slight camera ghost for atmosphere)
        dark_frame = (frame.astype(np.float32) * 0.08).astype(np.uint8)
        canvas     = dark_frame.copy()

        # ── Spawn particles ─────────────────────
        spawn_n = 6 if state == "open" else 8
        if len(particles) < PARTICLE_BUDGET:
            for _ in range(spawn_n):
                particles.append(Particle(cx, cy, state))

        # ── Update & draw particles ─────────────
        alive_p = []
        for p in particles:
            p.update()
            if p.alive():
                p.draw(canvas)
                alive_p.append(p)
        particles = alive_p

        # ── Draw main effect ────────────────────
        if state == "open":
            draw_3d_ring(canvas, cx, cy, t, alpha)
        else:
            draw_vortex(canvas, cx, cy, t, alpha)

        draw_glow_core(canvas, cx, cy, state, alpha)

        # ── Draw hand skeleton overlay ──────────
        if results.multi_hand_landmarks:
            lm = results.multi_hand_landmarks[0]
            connections = mp_hands.HAND_CONNECTIONS
            for conn in connections:
                a = lm.landmark[conn[0]]
                b = lm.landmark[conn[1]]
                pa = (int(a.x * WIDTH), int(a.y * HEIGHT))
                pb = (int(b.x * WIDTH), int(b.y * HEIGHT))
                cv2.line(canvas, pa, pb, (40, 40, 60), 1, cv2.LINE_AA)
            for lmk in lm.landmark:
                px = int(lmk.x * WIDTH)
                py = int(lmk.y * HEIGHT)
                cv2.circle(canvas, (px, py), 3, (80, 80, 120), -1, cv2.LINE_AA)

        # ── Shockwaves ──────────────────────────
        alive_sw = []
        for sw in shockwaves:
            sw.update()
            sw.draw(canvas)
            if sw.alive:
                alive_sw.append(sw)
        shockwaves = alive_sw

        # ── HUD ─────────────────────────────────
        draw_hud(canvas, state, fingers_count, fps, frozen)

        cv2.imshow(win_name, canvas)

    cap.release()
    cv2.destroyAllWindows()
    hands_det.close()
    print("Show ended.")


if __name__ == "__main__":
    main()
