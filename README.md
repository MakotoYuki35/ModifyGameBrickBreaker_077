# 🧱 Brick Breaker: Deluxe Arcade

An enhanced, retro-style Brick Breaker / Arkanoid game built in Python using **Pygame**. Features dynamic ball physics, dual laser cannons, multiple power-up drops, explosive TNT bricks, particle debris, and procedural/custom 8-bit sound effects.

---

## 🎮 Features

- **Dynamic Ball Physics:** Ball bounce angles reflect dynamically based on where the ball strikes the paddle (center vs. edges). True 4-way collision resolution prevents tunneling.
- **Controlled Launch / Serve:** Aim trajectory guide on round start, stage clear, and after losing a life. Launch with `SPACE` or `Left Click`.
- **Dual Controls:** Full support for both **Mouse tracking** and **Keyboard** (`A`/`D` or `Left`/`Right` arrow keys).
- **Power-Up System:**
  - 🟢 **WIDE (W):** Expands the paddle by 50% for 10 seconds.
  - 🟣 **MULTI (M):** Multiplies active balls into multiple simultaneous balls.
  - 🟡 **SLOW (S):** Slows down ball velocity for precise bank shots.
  - 🔴 **LIFE (L):** Restores 1 life (up to 5 hearts max).
  - ⚡ **FIRE (F):** Blazing fireball that pierces straight through bricks.
  - 🔫 **GUN (G):** Equips dual blasters onto the paddle to shoot upward lasers.
- **Special Bricks & Stages:**
  - **Multi-Hit Bricks:** Degrading colors: Red (3 hits) $\rightarrow$ Orange (2 hits) $\rightarrow$ Green (1 hit).
  - **Explosive TNT Bricks:** Area-of-effect explosion clearing adjacent bricks with fiery particles.
  - **Steel Bricks:** Indestructible metallic barriers.
  - **Moving Barriers:** Patrolling bricks that test your timing.
  - **Hand-Crafted & Procedural Stages:** Classic walls, pyramids, fortresses, and infinite procedural stages on level 4+.
- **Game Juice & Audio:**
  - Screen shake on TNT blasts and life losses.
  - Particle debris explosions tailored to brick colors.
  - Combo multiplier system with floating score popups.
  - Hybrid sound engine: loads local `.wav` files from `sounds/` or procedurally synthesizes 8-bit sounds in RAM.
  - Persistent high score saved to `highscore.json`.

---

## 🕹️ Controls

| Action | Control |
| :--- | :--- |
| **Move Paddle** | Mouse Movement **OR** `Left` / `Right` Arrow keys **OR** `A` / `D` |
| **Launch Ball / Shoot Lasers** | `SPACEBAR` **OR** `Left Mouse Click` |
| **Pause / Resume** | `P` |
| **Mute / Unmute Sound** | `M` |
| **Restart Game (on Game Over)** | `SPACEBAR` |
| **Quit Game** | `ESC` |

---

## 🚀 Installation & Running

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the game
```bash
python Brick_Breaker.py or & ".\.venv\Scripts\python.exe" "Brick_Breaker.py" (if the first option doesn't work)
```

---

## 📁 Project Structure

```text
├── Brick_Breaker.py    # Main game script
├── requirements.txt    # Python dependencies
├── README.md           # Documentation & instructions
├── .gitignore          # Ignores venv, cache, and local save files
└── sounds/             # 8-bit retro sound effects (.wav)
    ├── paddle.wav
    ├── brick.wav
    ├── break.wav
    ├── tnt.wav
    ├── steel.wav
    ├── laser.wav
    ├── powerup.wav
    ├── lose.wav
    └── win.wav
```

