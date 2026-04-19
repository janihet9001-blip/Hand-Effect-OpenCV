# HANDS OF NOTHING — OpenCV Magic Show System

A real-time hand gesture detection system that triggers different
3D visual effects based on your hand state. Built for live stage performance.

---

## What it does

| Hand State     | Effect                                              |
|----------------|-----------------------------------------------------|
| Open palm      | 3D golden orbiting rings + rising particle portal   |
| Closed fist    | Dark purple vortex spiral + collapsing particles    |
| Transition     | Shockwave ripple burst between states               |

---

## Setup

### 1. Install Python 3.9+
Download from https://python.org

### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Run the show
```
python main.py
```

---

## Controls

| Key     | Action                        |
|---------|-------------------------------|
| Q       | Quit                          |
| F       | Toggle fullscreen             |
| SPACE   | Freeze / unfreeze frame       |
| 1       | Force OPEN palm effect        |
| 2       | Force CLOSED fist effect      |

---

## Stage setup

```
[Webcam] → USB → [Laptop] → HDMI → [Projector] → [Stage screen/surface]
```

- Mount webcam above or in front of your performance area
- Point it down at your hands (overhead angle works best)
- Set projector to mirror/extend display and point at screen behind you
- Run fullscreen (press F) before performance

---

## Customise the effects

All config is at the top of `main.py`:

```python
WIDTH, HEIGHT = 1280, 720   # Change to 1920, 1080 for full HD
FULLSCREEN    = False        # Set True to auto-launch fullscreen
CAMERA_INDEX  = 0            # Change if using external webcam (try 1, 2)

OPEN_FINGERS_THRESHOLD  = 3  # Fingers needed to trigger OPEN effect
CLOSE_FINGERS_THRESHOLD = 1  # Fingers needed to trigger CLOSED effect
TRANSITION_FRAMES       = 18 # Speed of transition (lower = faster)
```

---

## Performance tips

- **Lighting:** Keep your hands well-lit. The system works best with even,
  warm lighting on your hands and dark background behind you.
- **Camera distance:** 60–90cm from hands is ideal.
- **Contrast:** Wear dark clothes so the hand detection stays clean.
- **Rehearse transitions:** The shockwave triggers on every open/close change —
  rehearse so your transitions land on musical cues.

---

## Files

```
magic_show/
├── main.py           ← Main application (run this)
├── Main-2.py           ← Main application (run this)
├── requirements.txt  ← Python dependencies
└── README.md         ← This file
```
