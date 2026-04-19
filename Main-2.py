"""
HANDS OF NOTHING v2 — OpenCV Magic Show System
================================================
6 gesture states, each with a unique colour & effect:

  0 fingers (fist)   → BLACK HOLE     — dark purple vortex collapse
  1 finger            → LIGHTNING      — electric blue arc storm
  2 fingers           → SMOKE          — grey/teal drifting smoke wisps
  3 fingers           → MATRIX RAIN    — green falling code rain
  4 fingers           → FIRE           — orange/red rising fire embers
  5 fingers (open)    → PORTAL         — gold orbiting 3D rings + particles

Every transition fires a colour-matched shockwave.

Run:   python main.py
Keys:  Q=quit  F=fullscreen  SPACE=freeze  H=toggle HUD  0-5=force gesture
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import math
import random

WIDTH, HEIGHT   = 1280, 720
CAMERA_INDEX    = 0
SHOW_HUD        = True
PARTICLE_BUDGET = 350
TRANS_SPEED     = 0.07

GESTURES = {
    0: ("BLACK HOLE",   (180,  0, 140),  ( 60,  0,  80)),
    1: ("LIGHTNING",    (255, 200,  50),  (100, 180, 255)),
    2: ("SMOKE",        (160, 180, 160),  ( 80, 120, 120)),
    3: ("MATRIX RAIN",  (  0, 220,  60),  (  0, 100,  30)),
    4: ("FIRE",         (  0, 100, 255),  (  0,  40, 180)),
    5: ("PORTAL",       (  0, 200, 255),  (  0, 100, 200)),
}


def hsv_to_bgr(h, s, v):
    h = h % 360
    hi = int(h / 60) % 6
    f  = h / 60 - int(h / 60)
    p  = v * (1 - s)
    q  = v * (1 - f * s)
    t  = v * (1 - (1 - f) * s)
    cols = [(v,t,p),(q,v,p),(p,v,t),(p,q,v),(t,p,v),(v,p,q)]
    r, g, b = cols[hi]
    return (int(b*255), int(g*255), int(r*255))


def alpha_color(color, a):
    return tuple(int(c * max(0.0, min(1.0, a))) for c in color)


class Shockwave:
    def __init__(self, cx, cy, gesture):
        self.cx = cx; self.cy = cy
        self.r = 0; self.max_r = math.hypot(WIDTH, HEIGHT)
        self.speed = 28; self.alive = True
        self.color = GESTURES[gesture][1]

    def update(self):
        self.r += self.speed
        if self.r > self.max_r: self.alive = False

    def draw(self, canvas):
        if not self.alive: return
        t = self.r / self.max_r
        a = max(0.0, 1.0 - t * 1.8)
        thick = max(1, int((1 - t) * 10))
        color = alpha_color(self.color, a)
        if a > 0.02:
            cv2.circle(canvas, (int(self.cx), int(self.cy)), int(self.r), color, thick, cv2.LINE_AA)
            cv2.circle(canvas, (int(self.cx), int(self.cy)), max(1, int(self.r * 0.85)),
                       alpha_color(self.color, a * 0.3), max(1, thick // 2), cv2.LINE_AA)


class Particle:
    def __init__(self, cx, cy, gesture):
        self.gesture = gesture
        self.hue_range = (0, 60)
        self.char = '0'
        self.spawn(cx, cy)

    def spawn(self, cx, cy):
        g = self.gesture
        self.life = random.uniform(0.6, 1.0)
        self.size = random.uniform(2, 6)
        if g == 0:
            angle = random.uniform(0, 2*math.pi)
            radius = random.uniform(100, 260)
            self.x = cx + math.cos(angle) * radius
            self.y = cy + math.sin(angle) * radius
            self.vx = (cx - self.x) * random.uniform(0.04, 0.08)
            self.vy = (cy - self.y) * random.uniform(0.04, 0.08)
            self.decay = random.uniform(0.018, 0.032)
            self.hue_range = (270, 310)
        elif g == 1:
            angle = random.uniform(0, 2*math.pi)
            speed = random.uniform(4, 12)
            self.x = cx + random.uniform(-10, 10)
            self.y = cy + random.uniform(-10, 10)
            self.vx = math.cos(angle) * speed + random.uniform(-2, 2)
            self.vy = math.sin(angle) * speed + random.uniform(-2, 2)
            self.decay = random.uniform(0.04, 0.09)
            self.size = random.uniform(1, 3)
            self.hue_range = (40, 60)
        elif g == 2:
            self.x = cx + random.uniform(-60, 60)
            self.y = cy + random.uniform(-20, 20)
            self.vx = random.uniform(-0.8, 0.8)
            self.vy = random.uniform(-1.8, -0.4)
            self.decay = random.uniform(0.006, 0.014)
            self.size = random.uniform(8, 22)
            self.hue_range = (160, 200)
        elif g == 3:
            self.x = random.uniform(0, WIDTH)
            self.y = random.uniform(-50, 0)
            self.vx = 0; self.vy = random.uniform(4, 12)
            self.decay = random.uniform(0.005, 0.015)
            self.size = random.uniform(1.5, 4)
            self.hue_range = (100, 130)
            self.char = chr(random.choice(list(range(0x30A0, 0x30FF)) + list(range(48, 58))))
        elif g == 4:
            self.x = cx + random.uniform(-70, 70)
            self.y = cy + random.uniform(0, 30)
            self.vx = random.uniform(-1.2, 1.2)
            self.vy = random.uniform(-4.5, -1.5)
            self.decay = random.uniform(0.012, 0.025)
            self.size = random.uniform(3, 9)
            self.hue_range = (0, 35)
        else:
            angle = random.uniform(0, 2*math.pi)
            speed = random.uniform(1.5, 4.5)
            self.x = cx + random.uniform(-20, 20)
            self.y = cy + random.uniform(-20, 20)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed - random.uniform(0.5, 2.0)
            self.decay = random.uniform(0.012, 0.022)
            self.size = random.uniform(2, 7)
            self.hue_range = (25, 55)

    def update(self):
        self.x += self.vx; self.y += self.vy
        self.life -= self.decay
        g = self.gesture
        if g == 0: self.vx *= 1.05; self.vy *= 1.05
        elif g == 1: self.vx *= 0.93; self.vy *= 0.93
        elif g == 2:
            self.vx += random.uniform(-0.15, 0.15)
            self.size = min(self.size + 0.15, 28)
        elif g == 4:
            self.vx += random.uniform(-0.2, 0.2)
            self.vy -= 0.08
            self.size = max(0.5, self.size * 0.97)

    def alive(self):
        return self.life > 0 and -20 < self.x < WIDTH+20 and -20 < self.y < HEIGHT+20

    def draw(self, canvas):
        a = max(0.0, self.life)
        r = max(1, int(self.size))
        h = random.uniform(*self.hue_range)
        color = alpha_color(hsv_to_bgr(h, 0.9, 1.0), a)
        if self.gesture == 3:
            cv2.putText(canvas, self.char, (int(self.x), int(self.y)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35,
                        alpha_color((0, 255, 80), a * 0.9), 1, cv2.LINE_AA)
        elif self.gesture == 2:
            ov = canvas.copy()
            cv2.circle(ov, (int(self.x), int(self.y)), r, color, -1, cv2.LINE_AA)
            cv2.addWeighted(ov, a * 0.25, canvas, 1 - a * 0.25, 0, canvas)
        else:
            cv2.circle(canvas, (int(self.x), int(self.y)), r, color, -1, cv2.LINE_AA)


def draw_blackhole(canvas, cx, cy, t, alpha):
    for arm in range(6):
        pts = []
        for i in range(140):
            s = i / 139.0
            angle = s * 5 * math.pi + (arm / 6) * 2 * math.pi + t * 2.8
            radius = s * 140 * (1 - s * 0.25)
            pts.append((int(cx + math.cos(angle) * radius),
                        int(cy + math.sin(angle) * radius * 0.5)))
        for i in range(len(pts)-1):
            fade = i / 140.0
            cv2.line(canvas, pts[i], pts[i+1],
                     alpha_color((160, 0, 120), alpha * fade), 1, cv2.LINE_AA)
    for layer in range(5, 0, -1):
        a = alpha * (1 - layer/6) * 0.8
        cv2.circle(canvas, (cx, cy), layer*10, alpha_color((80, 0, 60), a), -1, cv2.LINE_AA)


def draw_lightning(canvas, cx, cy, t, alpha):
    for bolt in range(7):
        angle = (bolt / 7) * 2 * math.pi + t * 1.5
        length = random.uniform(80, 220)
        ex = int(cx + math.cos(angle) * length)
        ey = int(cy + math.sin(angle) * length)
        pts = [(cx, cy)]
        steps = random.randint(5, 10)
        for s in range(1, steps):
            frac = s / steps
            pts.append((int(cx + (ex-cx)*frac + random.uniform(-20,20)),
                        int(cy + (ey-cy)*frac + random.uniform(-20,20))))
        pts.append((ex, ey))
        bright = alpha * random.uniform(0.6, 1.0)
        for i in range(len(pts)-1):
            cv2.line(canvas, pts[i], pts[i+1], alpha_color((255, 220, 80), bright), 2, cv2.LINE_AA)
            cv2.line(canvas, pts[i], pts[i+1], alpha_color((180, 200, 255), bright*0.5), 1, cv2.LINE_AA)
    for layer in range(6, 0, -1):
        a = alpha * (1 - layer/7) * 0.9
        cv2.circle(canvas, (cx, cy), layer*8, alpha_color((255, 230, 100), a), -1, cv2.LINE_AA)


def draw_smoke_base(canvas, cx, cy, t, alpha):
    for i in range(8):
        phase = t * 0.4 + i * 0.7
        ox = int(cx + math.sin(phase) * 30)
        oy = int(cy - i * 18 - (t * 20 % 80))
        r  = 20 + i * 12
        a  = alpha * max(0, 0.25 - i * 0.025)
        if a > 0.01:
            ov = canvas.copy()
            cv2.circle(ov, (ox, oy), r, alpha_color((140, 170, 150), 1.0), -1, cv2.LINE_AA)
            cv2.addWeighted(ov, a, canvas, 1-a, 0, canvas)


def draw_matrix_base(canvas, t, alpha):
    cols = 30
    step = WIDTH // cols
    for c in range(cols):
        x   = c * step + step // 2
        row = int((t * 8 + c * 3.7) % (HEIGHT // 14))
        y   = row * 14
        ch  = chr(random.choice(list(range(0x30A0, 0x30FF))))
        cv2.putText(canvas, ch, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.38,
                    alpha_color((180, 255, 180), alpha * 0.9), 1, cv2.LINE_AA)
        for tr in range(1, 6):
            ty = y - tr * 14
            if ty > 0:
                ch2 = chr(random.choice(list(range(0x30A0, 0x30FF))))
                cv2.putText(canvas, ch2, (x, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.32,
                            alpha_color((0, 180, 40), alpha * (1 - tr/6) * 0.5), 1, cv2.LINE_AA)


def draw_fire_base(canvas, cx, cy, t, alpha):
    for tongue in range(5):
        phase  = t * 3 + tongue * 1.2
        height = int(80 + 40 * abs(math.sin(phase)))
        ox     = int(cx + (tongue - 2) * 28)
        pts    = []
        for s in range(21):
            frac = s / 20
            wx = int(ox + math.sin(frac * math.pi * 2 + phase) * (1-frac) * 18)
            wy = int(cy - frac * height)
            pts.append((wx, wy))
        for i in range(len(pts)-1):
            frac = i / 20
            color = hsv_to_bgr(15 + frac * 25, 1.0, 1.0)
            cv2.line(canvas, pts[i], pts[i+1],
                     alpha_color(color, alpha * (1-frac) * 0.8),
                     max(1, int((1-frac) * 6)), cv2.LINE_AA)


def draw_portal_rings(canvas, cx, cy, t, alpha):
    for r in range(3):
        phase = t * (1.2 + r*0.3) + r * math.pi/3
        rx = 55 + r * 32
        ry = int(rx * abs(math.sin(phase + 0.3)) * 0.45 + 8)
        pts = []
        for i in range(61):
            angle = (i/60) * 2 * math.pi
            pts.append((int(cx + math.cos(angle) * rx),
                        int(cy + math.sin(angle + phase*0.5) * ry)))
        bright = int(220 * alpha * (0.6 + 0.4 * abs(math.cos(phase))))
        for i in range(len(pts)-1):
            cv2.line(canvas, pts[i], pts[i+1], (0, int(bright*0.5), bright), 1, cv2.LINE_AA)


def draw_glow_core(canvas, cx, cy, gesture, alpha):
    color = GESTURES[gesture][1]
    for i in range(7, 0, -1):
        a = alpha * (1 - i/8) * 0.85
        cv2.circle(canvas, (cx, cy), i*12, alpha_color(color, a), -1, cv2.LINE_AA)


def count_fingers(lm):
    count = 0
    if lm.landmark[4].x < lm.landmark[3].x: count += 1
    for tip, base in zip([8,12,16,20], [6,10,14,18]):
        if lm.landmark[tip].y < lm.landmark[base].y: count += 1
    return count


def palm_center(lm):
    return (int(np.mean([lm.landmark[i].x for i in [0,5,9,13,17]]) * WIDTH),
            int(np.mean([lm.landmark[i].y for i in [0,5,9,13,17]]) * HEIGHT))


def draw_skeleton(canvas, lm, mp_hands):
    for conn in mp_hands.HAND_CONNECTIONS:
        a = lm.landmark[conn[0]]; b = lm.landmark[conn[1]]
        cv2.line(canvas, (int(a.x*WIDTH), int(a.y*HEIGHT)),
                 (int(b.x*WIDTH), int(b.y*HEIGHT)), (35, 35, 55), 1, cv2.LINE_AA)
    for lmk in lm.landmark:
        cv2.circle(canvas, (int(lmk.x*WIDTH), int(lmk.y*HEIGHT)), 3, (70, 70, 110), -1, cv2.LINE_AA)


def draw_hud(canvas, gesture, fps, frozen):
    name, col, _ = GESTURES[gesture]
    cv2.putText(canvas, name, (18, 42), cv2.FONT_HERSHEY_SIMPLEX, 1.0, col, 2, cv2.LINE_AA)
    for i in range(6):
        cv2.circle(canvas, (18 + i*18, 62), 5,
                   col if i <= gesture else (40, 40, 50), -1, cv2.LINE_AA)
    cv2.putText(canvas, f"{fps:.0f} fps", (WIDTH-90, 38),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (70, 70, 70), 1, cv2.LINE_AA)
    hints = ["0-5:gesture", "F:fullscreen", "H:hud", "SPC:freeze", "Q:quit"]
    for i, h in enumerate(hints):
        cv2.putText(canvas, h, (18, HEIGHT-18-i*18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (55, 55, 55), 1, cv2.LINE_AA)
    if frozen:
        cv2.putText(canvas, "FROZEN", (WIDTH//2-45, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (80, 80, 200), 2, cv2.LINE_AA)


def main():
    mp_hands = mp.solutions.hands
    detector = mp_hands.Hands(static_image_mode=False, max_num_hands=1,
                               min_detection_confidence=0.7, min_tracking_confidence=0.6)
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    WIN = "HANDS OF NOTHING v2"
    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)

    gesture = 5; alpha = 1.0
    particles = []; shockwaves = []
    cx, cy = WIDTH//2, HEIGHT//2
    t = 0.0; prev_t = time.time(); fps = 30.0
    frozen = False; frozen_frame = None; show_hud = SHOW_HUD
    finger_history = [5]*6; hist_idx = 0
    canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

    print("\n  HANDS OF NOTHING v2")
    print("  0=BLACK HOLE  1=LIGHTNING  2=SMOKE")
    print("  3=MATRIX RAIN  4=FIRE  5=PORTAL\n")

    while True:
        now = time.time(); dt = now - prev_t; prev_t = now
        fps = 0.9*fps + 0.1/max(dt, 0.001); t += dt

        ret, frame = cap.read()
        if not ret: continue
        frame = cv2.flip(cv2.resize(frame, (WIDTH, HEIGHT)), 1)
        results = detector.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        raw_fingers = gesture
        if results.multi_hand_landmarks:
            lm = results.multi_hand_landmarks[0]
            raw_fingers = count_fingers(lm)
            cx, cy = palm_center(lm)

        finger_history[hist_idx % 6] = raw_fingers; hist_idx += 1
        smooth_fingers = max(set(finger_history), key=finger_history.count)

        if smooth_fingers != gesture:
            gesture = smooth_fingers; alpha = 0.0
            shockwaves.append(Shockwave(cx, cy, gesture))
            particles.clear()

        alpha = min(1.0, alpha + TRANS_SPEED * (fps / 30))

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): break
        elif key == ord('f'):
            prop = cv2.getWindowProperty(WIN, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(WIN, cv2.WND_PROP_FULLSCREEN,
                cv2.WINDOW_NORMAL if prop == cv2.WINDOW_FULLSCREEN else cv2.WINDOW_FULLSCREEN)
        elif key == ord('h'): show_hud = not show_hud
        elif key == ord(' '):
            frozen = not frozen
            if frozen: frozen_frame = canvas.copy()
        elif key in [ord(str(i)) for i in range(6)]:
            forced = key - ord('0')
            if forced != gesture:
                gesture = forced; alpha = 0.0
                shockwaves.append(Shockwave(cx, cy, gesture))
                particles.clear()

        if frozen and frozen_frame is not None:
            cv2.imshow(WIN, frozen_frame); continue

        canvas = (frame.astype(np.float32) * 0.07).astype(np.uint8)

        if gesture == 3: draw_matrix_base(canvas, t, alpha)

        spawn = 8 if gesture in (0, 4) else 5
        if len(particles) < PARTICLE_BUDGET:
            for _ in range(spawn):
                particles.append(Particle(cx, cy, gesture))

        live = []
        for p in particles:
            p.update()
            if p.alive(): p.draw(canvas); live.append(p)
        particles = live

        if   gesture == 0: draw_blackhole(canvas, cx, cy, t, alpha)
        elif gesture == 1: draw_lightning(canvas, cx, cy, t, alpha)
        elif gesture == 2: draw_smoke_base(canvas, cx, cy, t, alpha)
        elif gesture == 4: draw_fire_base(canvas, cx, cy, t, alpha)
        elif gesture == 5: draw_portal_rings(canvas, cx, cy, t, alpha)

        draw_glow_core(canvas, cx, cy, gesture, alpha)

        if results.multi_hand_landmarks:
            draw_skeleton(canvas, results.multi_hand_landmarks[0], mp_hands)

        live_sw = []
        for sw in shockwaves:
            sw.update(); sw.draw(canvas)
            if sw.alive: live_sw.append(sw)
        shockwaves = live_sw

        if show_hud: draw_hud(canvas, gesture, fps, frozen)

        cv2.imshow(WIN, canvas)

    cap.release(); cv2.destroyAllWindows(); detector.close()
    print("Show ended.")


if __name__ == "__main__":
    main()
