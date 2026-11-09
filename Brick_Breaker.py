import pygame
import random
import math
import io
import wave
import struct
import json
import os
from collections import deque

# ----------------- Initialization -----------------
pygame.init()

# Audio initialization
AUDIO_ENABLED = False
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    AUDIO_ENABLED = True
except Exception:
    AUDIO_ENABLED = False

# ----------------- Display & Configuration -----------------
WIDTH, HEIGHT = 660, 620
FPS = 60
BASE_DIR = os.path.dirname(__file__)
SOUNDS_DIR = os.path.join(BASE_DIR, "sounds")
HIGHSCORE_FILE = os.path.join(BASE_DIR, "highscore.json")

# Palette (Cyberpunk Neon Arcade)
BG_COLOR = (14, 16, 24)
PANEL_COLOR = (24, 28, 42)
BORDER_COLOR = (45, 52, 75)
WHITE = (255, 255, 255)
GRAY = (130, 138, 155)
GOLD = (255, 215, 0)

COLOR_PADDLE = (64, 224, 208)        # Cyan / Turquoise
COLOR_BALL = (255, 255, 255)
COLOR_FIREBALL = (255, 95, 30)       # Piercing Fireball
COLOR_LASER = (50, 255, 120)         # Paddle Laser Bolt

# Brick Colors
COLOR_HEALTH_3 = (245, 65, 75)       # Red
COLOR_HEALTH_2 = (255, 165, 30)      # Orange
COLOR_HEALTH_1 = (60, 220, 130)      # Emerald Green
COLOR_STEEL = (175, 185, 200)        # Unbreakable Metallic Silver
COLOR_TNT = (235, 45, 35)            # Explosive Bomb

# Power-Up Colors & Badges
POWERUP_COLORS = {
    'WIDE': (65, 185, 255),          # Expand paddle (W)
    'MULTI': (245, 90, 210),         # Multi-ball (M)
    'SLOW': (255, 215, 40),          # Slow-motion (S)
    'LIFE': (255, 70, 95),           # Extra life (L)
    'FIRE': (255, 105, 30),          # Fireball pierce (F)
    'GUN': (50, 255, 120),           # Dual laser blasters (G)
}

# Typography
font_small = pygame.font.SysFont('consolas', 14, bold=True)
font_hud = pygame.font.SysFont('consolas', 18, bold=True)
font_large = pygame.font.SysFont('consolas', 38, bold=True)
font_tnt = pygame.font.SysFont('consolas', 13, bold=True)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Brick Breaker: Deluxe Arcade")
clock = pygame.time.Clock()


# ----------------- Persistent High Score -----------------
def load_high_score():
    try:
        if os.path.exists(HIGHSCORE_FILE):
            with open(HIGHSCORE_FILE, 'r') as f:
                data = json.load(f)
                return int(data.get('high_score', 0))
    except Exception:
        pass
    return 0


def save_high_score(new_high):
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump({'high_score': int(new_high)}, f)
    except Exception:
        pass


# ----------------- Sound Manager (Disk Files + Procedural Fallback) -----------------
class SoundManager:
    """Loads .wav files from the 'sounds/' folder, with automatic procedural fallback."""
    def __init__(self, sound_dir=SOUNDS_DIR):
        self.sounds = {}
        self.muted = False
        if not AUDIO_ENABLED:
            return

        sound_names = ['paddle', 'brick', 'break', 'tnt', 'steel', 'laser', 'powerup', 'lose', 'win']
        for name in sound_names:
            file_path = os.path.join(sound_dir, f"{name}.wav")
            if os.path.exists(file_path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(file_path)
                    continue
                except Exception:
                    pass

            # Procedural fallback if audio file is not present
            self.sounds[name] = self._generate_fallback(name)

    def play(self, sound_name):
        if not self.muted and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception:
                pass

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted

    def _generate_fallback(self, name):
        try:
            if name == 'paddle':
                return self._create_sweep(450, 720, 0.05, 'square', 0.18)
            elif name == 'brick':
                return self._create_sweep(650, 880, 0.04, 'square', 0.15)
            elif name == 'break':
                return self._create_sweep(320, 110, 0.09, 'noise', 0.22)
            elif name == 'tnt':
                return self._create_sweep(180, 40, 0.35, 'noise', 0.35)
            elif name == 'steel':
                return self._create_sweep(850, 750, 0.04, 'square', 0.14)
            elif name == 'laser':
                return self._create_sweep(900, 300, 0.08, 'square', 0.15)
            elif name == 'powerup':
                return self._create_arpeggio([523, 659, 784, 1046], 0.05, 0.20)
            elif name == 'lose':
                return self._create_sweep(380, 100, 0.30, 'square', 0.25)
            elif name == 'win':
                return self._create_arpeggio([440, 554, 659, 880], 0.08, 0.22)
        except Exception:
            pass
        return None

    def _create_sweep(self, f_start, f_end, duration, wave_type='square', volume=0.2):
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            frames = bytearray()
            for i in range(n_samples):
                t = i / sample_rate
                progress = i / n_samples
                freq = f_start + (f_end - f_start) * progress
                envelope = 1.0 - progress
                if wave_type == 'square':
                    val = 1.0 if (t * freq) % 1.0 < 0.5 else -1.0
                elif wave_type == 'noise':
                    val = random.uniform(-1.0, 1.0)
                else:
                    val = math.sin(2 * math.pi * freq * t)
                sample = int(val * volume * envelope * 32767)
                frames.extend(struct.pack('<h', max(-32768, min(32767, sample))))
            wf.writeframes(frames)
        buf.seek(0)
        return pygame.mixer.Sound(buf)

    def _create_arpeggio(self, freqs, note_duration, volume=0.2):
        sample_rate = 22050
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            frames = bytearray()
            for f in freqs:
                n_samples = int(sample_rate * note_duration)
                for i in range(n_samples):
                    t = i / sample_rate
                    val = 1.0 if (t * f) % 1.0 < 0.5 else -1.0
                    env = 1.0 - (i / n_samples)
                    sample = int(val * volume * env * 32767)
                    frames.extend(struct.pack('<h', max(-32768, min(32767, sample))))
            wf.writeframes(frames)
        buf.seek(0)
        return pygame.mixer.Sound(buf)


sound_manager = SoundManager()


# ----------------- Visual Juice: Particles & Text Floaters -----------------
class Particle:
    def __init__(self, x, y, color, is_fire=False):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2.0, 5.5) if not is_fire else random.uniform(1.0, 3.5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.size = random.randint(3, 6) if not is_fire else random.randint(2, 4)
        self.life = 1.0
        self.decay = random.uniform(0.025, 0.05)
        self.gravity = 0.12 if not is_fire else -0.05

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= self.decay

    def draw(self, surface):
        if self.life > 0:
            s = max(1, int(self.size * self.life))
            pygame.draw.rect(surface, self.color, (int(self.x), int(self.y), s, s))


class FloatingText:
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 1.0
        self.decay = 0.025

    def update(self):
        self.y -= 1.0
        self.life -= self.decay

    def draw(self, surface):
        if self.life > 0:
            surf = font_small.render(self.text, True, self.color)
            surf.set_alpha(int(self.life * 255))
            surface.blit(surf, (self.x - surf.get_width() // 2, self.y))


# ----------------- Laser Projectiles -----------------
class LaserBeam:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 4
        self.height = 14
        self.speed = 10.0
        self.color = COLOR_LASER

    def update(self):
        self.y -= self.speed

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y, self.width, self.height)

    def draw(self, surface):
        rect = self.get_rect()
        pygame.draw.rect(surface, self.color, rect, border_radius=2)
        core = pygame.Rect(self.x - 1, self.y + 2, 2, self.height - 4)
        pygame.draw.rect(surface, WHITE, core)


# ----------------- Power-Up Capsule -----------------
class PowerUp:
    def __init__(self, x, y, p_type):
        self.x = x
        self.y = y
        self.type = p_type  # 'WIDE', 'MULTI', 'SLOW', 'LIFE', 'FIRE', 'GUN'
        self.radius = 13
        self.speed = 2.4
        self.color = POWERUP_COLORS[self.type]

    def update(self):
        self.y += self.speed

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 2)
        letter = self.type[0]
        lbl = font_small.render(letter, True, (15, 17, 26))
        surface.blit(lbl, (self.x - lbl.get_width() // 2, self.y - lbl.get_height() // 2))


# ----------------- Striker (Paddle) -----------------
class Striker:
    def __init__(self, x, y, width=105, height=16, speed=8.5):
        self.base_width = width
        self.width = width
        self.height = height
        self.posx = x
        self.posy = y
        self.speed = speed
        self.expand_timer = 0
        self.gun_timer = 0
        self.gun_cooldown = 0

    def update(self, direction):
        self.posx += self.speed * direction

        if self.posx < 12:
            self.posx = 12
        elif self.posx + self.width > WIDTH - 12:
            self.posx = WIDTH - 12 - self.width

        if self.expand_timer > 0:
            self.expand_timer -= 1
            if self.expand_timer <= 0:
                self.width = self.base_width

        if self.gun_timer > 0:
            self.gun_timer -= 1

        if self.gun_cooldown > 0:
            self.gun_cooldown -= 1

    def set_position(self, target_center_x):
        self.posx = target_center_x - self.width // 2
        if self.posx < 12:
            self.posx = 12
        elif self.posx + self.width > WIDTH - 12:
            self.posx = WIDTH - 12 - self.width

    def expand(self, duration_frames=600):
        self.width = int(self.base_width * 1.5)
        self.expand_timer = duration_frames

    def enable_guns(self, duration_frames=600):
        self.gun_timer = duration_frames

    def shoot(self, lasers):
        if self.gun_timer > 0 and self.gun_cooldown <= 0:
            self.gun_cooldown = 14
            lasers.append(LaserBeam(self.posx + 6, self.posy))
            lasers.append(LaserBeam(self.posx + self.width - 6, self.posy))
            sound_manager.play('laser')

    def get_rect(self):
        return pygame.Rect(int(self.posx), int(self.posy), self.width, self.height)

    def draw(self, surface):
        rect = self.get_rect()
        paddle_color = (100, 245, 220) if self.expand_timer > 0 else COLOR_PADDLE

        if self.gun_timer > 0:
            cannon_left = pygame.Rect(self.posx + 3, self.posy - 6, 6, 8)
            cannon_right = pygame.Rect(self.posx + self.width - 9, self.posy - 6, 6, 8)
            pygame.draw.rect(surface, COLOR_LASER, cannon_left, border_radius=2)
            pygame.draw.rect(surface, COLOR_LASER, cannon_right, border_radius=2)

        pygame.draw.rect(surface, paddle_color, rect, border_radius=8)
        highlight = pygame.Rect(self.posx + 6, self.posy + 3, max(1, self.width - 12), 4)
        pygame.draw.rect(surface, (255, 255, 255), highlight, border_radius=3)


# ----------------- Ball Class -----------------
class Ball:
    def __init__(self, radius=7, base_speed=6.2):
        self.radius = radius
        self.base_speed = base_speed
        self.speed = base_speed
        self.trail = deque(maxlen=6)
        self.stuck = True
        self.posx = 0
        self.posy = 0
        self.vx = 0.0
        self.vy = 0.0
        self.is_fireball = False
        self.fireball_timer = 0
        self.aim_angle = 0.0

    def reset_on_paddle(self, striker):
        self.stuck = True
        self.speed = self.base_speed
        self.posx = striker.posx + striker.width // 2
        self.posy = striker.posy - self.radius - 2
        self.vx = 0.0
        self.vy = 0.0
        self.trail.clear()
        self.is_fireball = False
        self.fireball_timer = 0
        self.aim_angle = 0.0

    def launch(self):
        if self.stuck:
            self.stuck = False
            self.vx = self.speed * math.sin(self.aim_angle)
            self.vy = -abs(self.speed * math.cos(self.aim_angle))

    def update(self, striker):
        if self.stuck:
            self.posx = striker.posx + striker.width // 2
            self.posy = striker.posy - self.radius - 2
            self.aim_angle = math.sin(pygame.time.get_ticks() * 0.0035) * math.radians(45)
            return False

        if self.fireball_timer > 0:
            self.fireball_timer -= 1
            if self.fireball_timer <= 0:
                self.is_fireball = False

        self.trail.append((self.posx, self.posy))
        self.posx += self.vx
        self.posy += self.vy

        # Left / Right Wall Bounce
        if self.posx - self.radius <= 10:
            self.posx = 10 + self.radius
            self.vx = abs(self.vx)
            sound_manager.play('brick')
        elif self.posx + self.radius >= WIDTH - 10:
            self.posx = WIDTH - 10 - self.radius
            self.vx = -abs(self.vx)
            sound_manager.play('brick')

        # Top Bar Boundary Bounce
        if self.posy - self.radius <= 48:
            self.posy = 48 + self.radius
            self.vy = abs(self.vy)
            sound_manager.play('brick')

        # Bottom death boundary
        if self.posy - self.radius > HEIGHT:
            return True

        return False

    def bounce_paddle(self, striker):
        paddle_center = striker.posx + striker.width / 2
        offset = (self.posx - paddle_center) / (striker.width / 2)
        offset = max(-1.0, min(1.0, offset))

        angle = offset * math.radians(65)
        self.vx = self.speed * math.sin(angle)
        self.vy = -abs(self.speed * math.cos(angle))

        self.posy = striker.posy - self.radius - 1
        sound_manager.play('paddle')

    def bounce_block(self, block_rect):
        if self.is_fireball:
            return

        ball_rect = self.get_rect()
        overlap_l = ball_rect.right - block_rect.left
        overlap_r = block_rect.right - ball_rect.left
        overlap_t = ball_rect.bottom - block_rect.top
        overlap_b = block_rect.bottom - ball_rect.top

        min_x = min(overlap_l, overlap_r)
        min_y = min(overlap_t, overlap_b)

        if min_x < min_y:
            self.vx *= -1
            if overlap_l < overlap_r:
                self.posx = block_rect.left - self.radius
            else:
                self.posx = block_rect.right + self.radius
        else:
            self.vy *= -1
            if overlap_t < overlap_b:
                self.posy = block_rect.top - self.radius
            else:
                self.posy = block_rect.bottom + self.radius

    def enable_fireball(self, duration=360):
        self.is_fireball = True
        self.fireball_timer = duration

    def get_rect(self):
        return pygame.Rect(
            int(self.posx - self.radius),
            int(self.posy - self.radius),
            self.radius * 2,
            self.radius * 2
        )

    def draw(self, surface):
        color = COLOR_FIREBALL if self.is_fireball else COLOR_BALL

        if self.stuck:
            for d in range(15, 90, 10):
                gx = self.posx + d * math.sin(self.aim_angle)
                gy = self.posy - d * math.cos(self.aim_angle)
                pygame.draw.circle(surface, (140, 160, 200), (int(gx), int(gy)), 2)

        for i, pos in enumerate(self.trail):
            fade_r = max(1, int(self.radius * (i + 1) / (len(self.trail) + 2)))
            trail_color = (255, 140, 50) if self.is_fireball else (70, 95, 140)
            pygame.draw.circle(surface, trail_color, (int(pos[0]), int(pos[1])), fade_r)

        pygame.draw.circle(surface, color, (int(self.posx), int(self.posy)), self.radius)
        if self.is_fireball:
            pygame.draw.circle(surface, (255, 230, 80), (int(self.posx), int(self.posy)), self.radius // 2)


# ----------------- Brick Class -----------------
class Block:
    def __init__(self, x, y, width, height, health, is_steel=False, is_tnt=False, powerup_type=None, moving_range=0):
        self.x = x
        self.y = y
        self.start_x = x
        self.width = width
        self.height = height
        self.health = health
        self.max_health = health
        self.is_steel = is_steel
        self.is_tnt = is_tnt
        self.powerup_type = powerup_type
        self.moving_range = moving_range
        self.move_speed = 1.2 if moving_range > 0 else 0
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self):
        if self.moving_range > 0:
            self.x += self.move_speed
            if abs(self.x - self.start_x) >= self.moving_range:
                self.move_speed *= -1
            self.rect.x = int(self.x)

    def hit(self, damage=1):
        if self.is_steel:
            sound_manager.play('steel')
            return False

        self.health -= damage
        if self.health <= 0:
            return True
        else:
            sound_manager.play('brick')
            return False

    def get_color(self):
        if self.is_steel:
            return COLOR_STEEL
        if self.is_tnt:
            return COLOR_TNT
        if self.health >= 3:
            return COLOR_HEALTH_3
        elif self.health == 2:
            return COLOR_HEALTH_2
        else:
            return COLOR_HEALTH_1

    def draw(self, surface):
        color = self.get_color()
        pygame.draw.rect(surface, color, self.rect, border_radius=4)

        if self.is_steel:
            pygame.draw.circle(surface, (230, 235, 250), (self.rect.x + 5, self.rect.y + 5), 2)
            pygame.draw.circle(surface, (230, 235, 250), (self.rect.x + self.width - 6, self.rect.y + 5), 2)
            pygame.draw.circle(surface, (230, 235, 250), (self.rect.x + 5, self.rect.y + self.height - 6), 2)
            pygame.draw.circle(surface, (230, 235, 250), (self.rect.x + self.width - 6, self.rect.y + self.height - 6), 2)
        elif self.is_tnt:
            txt = font_tnt.render("TNT", True, WHITE)
            surface.blit(txt, (self.rect.x + self.width // 2 - txt.get_width() // 2,
                               self.rect.y + self.height // 2 - txt.get_height() // 2))
        else:
            border = (255, 255, 255) if self.powerup_type else (color[0] // 2, color[1] // 2, color[2] // 2)
            pygame.draw.rect(surface, border, self.rect, width=1, border_radius=4)
            highlight = pygame.Rect(self.rect.x + 2, self.rect.y + 2, self.width - 4, 3)
            pygame.draw.rect(surface, (255, 255, 255), highlight, border_radius=2)


# ----------------- Stage Layouts -----------------
def create_stage(level):
    blocks = []
    block_w, block_h = 56, 20
    gap_x, gap_y = 7, 7
    start_y = 70
    cols = (WIDTH - 40) // (block_w + gap_x)
    start_x = (WIDTH - (cols * (block_w + gap_x) - gap_x)) // 2

    powerups_pool = ['WIDE', 'MULTI', 'SLOW', 'LIFE', 'FIRE', 'GUN']

    if level == 1:
        # Classic Arcade Wall
        for r in range(5):
            for c in range(cols):
                x = start_x + c * (block_w + gap_x)
                y = start_y + r * (block_h + gap_y)
                health = 3 if r == 0 else (2 if r in (1, 2) else 1)
                p_type = random.choice(powerups_pool) if random.random() < 0.20 else None
                is_tnt = (r == 2 and c in (2, cols - 3))
                blocks.append(Block(x, y, block_w, block_h, health, is_tnt=is_tnt, powerup_type=p_type))

    elif level == 2:
        # Diamond / Pyramid Formation
        mid_col = cols // 2
        for r in range(7):
            span = r if r <= 3 else (6 - r)
            for c in range(mid_col - span, mid_col + span + 1):
                x = start_x + c * (block_w + gap_x)
                y = start_y + r * (block_h + gap_y)
                health = 3 if (r in (0, 6) or c in (mid_col - span, mid_col + span)) else 2
                is_tnt = (r == 3 and c == mid_col)
                p_type = random.choice(powerups_pool) if random.random() < 0.22 else None
                blocks.append(Block(x, y, block_w, block_h, health, is_tnt=is_tnt, powerup_type=p_type))

    elif level == 3:
        # Fortress with Steel Pillars & Moving Barrier
        for r in range(7):
            for c in range(cols):
                x = start_x + c * (block_w + gap_x)
                y = start_y + r * (block_h + gap_y)
                is_steel = (r in (2, 3) and c in (1, 4, cols - 2, cols - 5))
                is_tnt = (r == 1 and c in (cols // 2 - 1, cols // 2 + 1))
                health = 3 if r <= 2 else (2 if r <= 4 else 1)
                p_type = random.choice(powerups_pool) if (not is_steel and random.random() < 0.22) else None
                blocks.append(Block(x, y, block_w, block_h, health, is_steel=is_steel, is_tnt=is_tnt, powerup_type=p_type))

        blocks.append(Block(WIDTH // 2 - block_w // 2, start_y + 8 * (block_h + gap_y),
                            block_w, block_h, health=2, moving_range=90))

    else:
        # Procedural Geometric Stages for Level 4+
        rows = min(8, 5 + (level - 3))
        for r in range(rows):
            for c in range(cols):
                mirrored_c = min(c, cols - 1 - c)
                pattern = (r + mirrored_c) % 2 == 0 or (r % 2 == 0)
                if pattern:
                    x = start_x + c * (block_w + gap_x)
                    y = start_y + r * (block_h + gap_y)
                    is_steel = (r == 0 and mirrored_c == 0)
                    is_tnt = (r == 2 and mirrored_c == 1)
                    health = random.choice([2, 3]) if r < 3 else random.choice([1, 2])
                    p_type = random.choice(powerups_pool) if (not is_steel and random.random() < 0.25) else None
                    blocks.append(Block(x, y, block_w, block_h, health, is_steel=is_steel, is_tnt=is_tnt, powerup_type=p_type))

        blocks.append(Block(WIDTH // 2 - block_w // 2, start_y + (rows + 1) * (block_h + gap_y),
                            block_w, block_h, health=3, moving_range=120))

    return blocks


# ----------------- Main Game Loop -----------------
def main():
    running = True
    lives = 3
    score = 0
    high_score = load_high_score()
    level = 1
    combo = 0

    striker = Striker(WIDTH // 2 - 52, HEIGHT - 42)
    balls = [Ball(radius=7, base_speed=6.2)]
    balls[0].reset_on_paddle(striker)

    blocks = create_stage(level)
    particles = []
    powerups = []
    lasers = []
    floating_texts = []

    striker_dir = 0
    slow_timer = 0
    screen_shake = 0
    game_state = "PLAYING"

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                # Pause Toggle
                if event.key == pygame.K_p and game_state in ("PLAYING", "PAUSED"):
                    game_state = "PAUSED" if game_state == "PLAYING" else "PLAYING"

                # Sound Mute Toggle
                if event.key == pygame.K_m:
                    is_muted = sound_manager.toggle_mute()
                    msg = "SFX: MUTED" if is_muted else "SFX: ENABLED"
                    floating_texts.append(FloatingText(WIDTH // 2, 80, msg, GOLD))

                if game_state == "PLAYING":
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        striker_dir = -1
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        striker_dir = 1
                    elif event.key == pygame.K_SPACE:
                        if any(b.stuck for b in balls):
                            for b in balls:
                                b.launch()
                        else:
                            striker.shoot(lasers)

                elif game_state in ("GAMEOVER", "VICTORY"):
                    if event.key == pygame.K_SPACE:
                        if game_state == "GAMEOVER":
                            lives = 3
                            score = 0
                            level = 1
                        else:
                            level += 1

                        striker = Striker(WIDTH // 2 - 52, HEIGHT - 42)
                        new_ball_speed = min(9.5, 6.2 + (level - 1) * 0.4)
                        balls = [Ball(radius=7, base_speed=new_ball_speed)]
                        balls[0].reset_on_paddle(striker)
                        blocks = create_stage(level)
                        particles.clear()
                        powerups.clear()
                        lasers.clear()
                        floating_texts.clear()
                        combo = 0
                        game_state = "PLAYING"

                    elif event.key == pygame.K_ESCAPE:
                        running = False

            if event.type == pygame.KEYUP and game_state == "PLAYING":
                if event.key in (pygame.K_LEFT, pygame.K_a) and striker_dir == -1:
                    striker_dir = 0
                elif event.key in (pygame.K_RIGHT, pygame.K_d) and striker_dir == 1:
                    striker_dir = 0

            # Mouse Paddle Control & Click to Launch/Fire
            if event.type == pygame.MOUSEMOTION and game_state == "PLAYING":
                striker.set_position(event.pos[0])

            if event.type == pygame.MOUSEBUTTONDOWN and game_state == "PLAYING":
                if event.button == 1:
                    if any(b.stuck for b in balls):
                        for b in balls:
                            b.launch()
                    else:
                        striker.shoot(lasers)

        # ----------------- Physics & Game Logic -----------------
        if game_state == "PLAYING":
            striker.update(striker_dir)

            for bk in blocks:
                bk.update()

            if slow_timer > 0:
                slow_timer -= 1
                if slow_timer <= 0:
                    for b in balls:
                        b.speed = b.base_speed

            # Lasers update
            for laser in lasers[:]:
                laser.update()
                if laser.y < 46:
                    lasers.remove(laser)
                    continue

                for block in blocks[:]:
                    if laser.get_rect().colliderect(block.rect):
                        lasers.remove(laser)
                        destroyed = block.hit()
                        for _ in range(5):
                            particles.append(Particle(laser.x, laser.y, COLOR_LASER))

                        if destroyed:
                            pts = block.max_health * 15
                            score += pts
                            floating_texts.append(FloatingText(block.rect.centerx, block.rect.centery, f"+{pts}", COLOR_LASER))
                            if block.powerup_type:
                                powerups.append(PowerUp(block.rect.centerx, block.rect.centery, block.powerup_type))
                            blocks.remove(block)
                            sound_manager.play('break')
                        break

            # Balls update
            balls_lost = []
            for b in balls:
                is_lost = b.update(striker)
                if is_lost:
                    balls_lost.append(b)

            for b in balls_lost:
                balls.remove(b)

            if not balls:
                lives -= 1
                combo = 0
                screen_shake = 12
                sound_manager.play('lose')

                if lives <= 0:
                    game_state = "GAMEOVER"
                    if score > high_score:
                        high_score = score
                        save_high_score(high_score)
                else:
                    new_speed = min(9.5, 6.2 + (level - 1) * 0.4)
                    new_ball = Ball(radius=7, base_speed=new_speed)
                    new_ball.reset_on_paddle(striker)
                    balls.append(new_ball)

            # Ball-Paddle Collision
            for b in balls:
                if not b.stuck and b.get_rect().colliderect(striker.get_rect()):
                    b.bounce_paddle(striker)
                    combo = 0

            # Ball-Block Collision
            for b in balls:
                if b.stuck:
                    continue

                for block in blocks[:]:
                    if b.get_rect().colliderect(block.rect):
                        b.bounce_block(block.rect)
                        destroyed = block.hit()

                        for _ in range(7):
                            particles.append(Particle(block.rect.centerx, block.rect.centery, block.get_color()))

                        if destroyed:
                            combo += 1
                            combo_bonus = (combo - 1) * 10
                            pts = (block.max_health * 15) + combo_bonus
                            score += pts

                            txt = f"+{pts}" if combo <= 1 else f"+{pts} (x{combo} Combo!)"
                            txt_color = GOLD if combo > 2 else WHITE
                            floating_texts.append(FloatingText(block.rect.centerx, block.rect.y, txt, txt_color))

                            if block.is_tnt:
                                sound_manager.play('tnt')
                                screen_shake = 16
                                explosion_radius = 85
                                for adj in blocks[:]:
                                    if not adj.is_steel and math.hypot(adj.rect.centerx - block.rect.centerx,
                                                                       adj.rect.centery - block.rect.centery) < explosion_radius:
                                        if adj != block:
                                            for _ in range(8):
                                                particles.append(Particle(adj.rect.centerx, adj.rect.centery, adj.get_color(), is_fire=True))
                                            blocks.remove(adj)
                                            score += 15

                                for _ in range(25):
                                    particles.append(Particle(block.rect.centerx, block.rect.centery, (255, 120, 20), is_fire=True))
                            else:
                                sound_manager.play('break')

                            if block.powerup_type:
                                powerups.append(PowerUp(block.rect.centerx, block.rect.centery, block.powerup_type))

                            if block in blocks:
                                blocks.remove(block)
                        break

            # Power-Up Movement & Catching
            for p in powerups[:]:
                p.update()
                if p.get_rect().colliderect(striker.get_rect()):
                    sound_manager.play('powerup')
                    floating_texts.append(FloatingText(striker.posx + striker.width // 2, striker.posy - 12,
                                                       f"{p.type} POWER-UP!", p.color))

                    if p.type == 'WIDE':
                        striker.expand()
                    elif p.type == 'GUN':
                        striker.enable_guns()
                    elif p.type == 'MULTI':
                        extra_balls = []
                        for b in balls:
                            if not b.stuck:
                                b1 = Ball(radius=b.radius, base_speed=b.speed)
                                b1.posx, b1.posy = b.posx, b.posy
                                b1.vx = -b.vx * 0.9 if b.vx != 0 else 3.0
                                b1.vy = b.vy
                                b1.stuck = False
                                b1.is_fireball = b.is_fireball
                                extra_balls.append(b1)
                        balls.extend(extra_balls[:2])
                    elif p.type == 'SLOW':
                        slow_timer = 450
                        for b in balls:
                            b.speed = max(3.5, b.base_speed * 0.65)
                    elif p.type == 'LIFE':
                        lives = min(5, lives + 1)
                    elif p.type == 'FIRE':
                        for b in balls:
                            b.enable_fireball()

                    powerups.remove(p)
                elif p.y > HEIGHT:
                    powerups.remove(p)

            # Check for Stage Victory
            destructible_remaining = [bk for bk in blocks if not bk.is_steel]
            if not destructible_remaining:
                game_state = "VICTORY"
                sound_manager.play('win')
                score += 250 * level
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)

        # Update visuals
        for pt in particles[:]:
            pt.update()
            if pt.life <= 0:
                particles.remove(pt)

        for ft in floating_texts[:]:
            ft.update()
            if ft.life <= 0:
                floating_texts.remove(ft)

        # ----------------- Rendering -----------------
        shake_x, shake_y = 0, 0
        if screen_shake > 0:
            shake_x = random.randint(-screen_shake, screen_shake)
            shake_y = random.randint(-screen_shake, screen_shake)
            screen_shake -= 1

        render_surface = pygame.Surface((WIDTH, HEIGHT))
        render_surface.fill(BG_COLOR)

        # Draw HUD Panel
        pygame.draw.rect(render_surface, PANEL_COLOR, (0, 0, WIDTH, 46))
        pygame.draw.line(render_surface, BORDER_COLOR, (0, 46), (WIDTH, 46), 2)

        # HUD Info
        sc_lbl = font_hud.render(f"SCORE: {score}", True, WHITE)
        render_surface.blit(sc_lbl, (16, 13))

        hi_lbl = font_small.render(f"HIGH: {high_score}", True, GRAY)
        render_surface.blit(hi_lbl, (170, 16))

        lvl_lbl = font_hud.render(f"STAGE {level}", True, COLOR_PADDLE)
        render_surface.blit(lvl_lbl, (WIDTH // 2 - lvl_lbl.get_width() // 2, 13))

        # Hearts for Lives
        heart_symbols = "♥ " * lives
        lives_lbl = font_hud.render(f"LIVES: {heart_symbols}", True, (255, 80, 105))
        render_surface.blit(lives_lbl, (WIDTH - lives_lbl.get_width() - 16, 13))

        # Active Power-Up Timers Bar (Directly below HUD)
        timer_x = 16
        if striker.expand_timer > 0:
            pct = striker.expand_timer / 600
            pygame.draw.rect(render_surface, POWERUP_COLORS['WIDE'], (timer_x, 48, int(60 * pct), 3))
            timer_x += 70
        if striker.gun_timer > 0:
            pct = striker.gun_timer / 600
            pygame.draw.rect(render_surface, POWERUP_COLORS['GUN'], (timer_x, 48, int(60 * pct), 3))
            timer_x += 70
        if slow_timer > 0:
            pct = slow_timer / 450
            pygame.draw.rect(render_surface, POWERUP_COLORS['SLOW'], (timer_x, 48, int(60 * pct), 3))
            timer_x += 70
        fireball_active = any(b.fireball_timer > 0 for b in balls)
        if fireball_active:
            max_fb = max(b.fireball_timer for b in balls)
            pct = max_fb / 360
            pygame.draw.rect(render_surface, POWERUP_COLORS['FIRE'], (timer_x, 48, int(60 * pct), 3))

        # Draw Blocks
        for bk in blocks:
            bk.draw(render_surface)

        # Draw Power-Ups
        for p in powerups:
            p.draw(render_surface)

        # Draw Lasers
        for laser in lasers:
            laser.draw(render_surface)

        # Draw Particles & Floating Text
        for pt in particles:
            pt.draw(render_surface)

        for ft in floating_texts:
            ft.draw(render_surface)

        # Draw Striker & Balls
        striker.draw(render_surface)
        for b in balls:
            b.draw(render_surface)

        # Launch Hint when ball is glued to striker
        if any(b.stuck for b in balls) and game_state == "PLAYING":
            hint = font_small.render("AIM & PRESS SPACE OR LEFT CLICK TO LAUNCH", True, GRAY)
            render_surface.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 75))

        # Overlays: PAUSE, GAMEOVER, VICTORY
        if game_state in ("PAUSED", "GAMEOVER", "VICTORY"):
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 14, 22, 215))
            render_surface.blit(overlay, (0, 0))

            if game_state == "PAUSED":
                title = font_large.render("PAUSED", True, WHITE)
                sub = font_small.render("Press P to Resume Game", True, GRAY)
            elif game_state == "GAMEOVER":
                title = font_large.render("GAME OVER", True, (255, 70, 70))
                sub = font_small.render(f"Final Score: {score}  |  Press SPACE to Retry  |  ESC to Quit", True, WHITE)
            else:
                title = font_large.render("STAGE CLEAR!", True, (70, 235, 140))
                sub = font_small.render(f"Bonus: +{250 * level} pts  |  Press SPACE for Next Stage", True, WHITE)

            render_surface.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 40))
            render_surface.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 25))

        screen.blit(render_surface, (shake_x, shake_y))
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
