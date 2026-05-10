import pygame
import random
import math
from core.settings import W, H, STAR_COUNT, YELLOW, ORANGE, RED, WHITE, BLUE, CYAN


# ── Starfield ─────────────────────────────────────────────────────────────
class Star:
    def __init__(self, initial=False):
        self.reset(initial)

    def reset(self, initial=False):
        self.x     = random.randint(0, W) if initial else float(W + 2)
        self.y     = random.uniform(0, H)
        self.speed = random.uniform(0.4, 3.5)
        self.size  = 1 if self.speed < 1.2 else (2 if self.speed < 2.5 else 3)
        b          = int(60 + self.speed * 50)
        self.color = (b, b, min(255, b + 40))

    def update(self):
        self.x -= self.speed
        if self.x < -4:
            self.reset()

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, (int(self.x), int(self.y), self.size, self.size))


class StarField:
    def __init__(self):
        self.stars = [Star(initial=True) for _ in range(STAR_COUNT)]

    def update(self):
        for s in self.stars:
            s.update()

    def draw(self, surf):
        for s in self.stars:
            s.draw(surf)


# ── Particle ──────────────────────────────────────────────────────────────
class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color, count=12, speed_range=(1, 5), life_range=(20, 45)):
        super().__init__()
        # Particle pool — each Particle sprite IS one particle
        self.particles = []
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spd   = random.uniform(*speed_range)
            life  = random.randint(*life_range)
            size  = random.randint(2, 6)
            self.particles.append({
                'x': float(x), 'y': float(y),
                'vx': math.cos(angle) * spd,
                'vy': math.sin(angle) * spd,
                'life': life, 'max_life': life,
                'size': size, 'color': color,
            })
        # Dummy image/rect for sprite group compatibility
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(center=(x, y))
        self._alive = True

    def update(self):
        alive = []
        for p in self.particles:
            p['x']  += p['vx']
            p['y']  += p['vy']
            p['vx'] *= 0.93
            p['vy'] *= 0.93
            p['life'] -= 1
            if p['life'] > 0:
                alive.append(p)
        self.particles = alive
        if not alive:
            self.kill()

    def draw(self, surf):
        for p in self.particles:
            alpha = p['life'] / p['max_life']
            size  = max(1, int(p['size'] * alpha))
            c     = tuple(int(ch * alpha) for ch in p['color'])
            pygame.draw.circle(surf, c, (int(p['x']), int(p['y'])), size)


# ── Explosion ─────────────────────────────────────────────────────────────
class Explosion(pygame.sprite.Sprite):
    def __init__(self, cx, cy, size=40, color=None):
        super().__init__()
        self.cx     = cx
        self.cy     = cy
        self.max_r  = size
        self.r      = 2
        self.age    = 0
        self.life   = 18
        self.color  = color or ORANGE
        self.image  = pygame.Surface((size * 2 + 4, size * 2 + 4), pygame.SRCALPHA)
        self.rect   = self.image.get_rect(center=(cx, cy))

    def update(self):
        self.age += 1
        self.r    = int(self.max_r * (self.age / self.life))
        if self.age >= self.life:
            self.kill()
            return
        self.image.fill((0, 0, 0, 0))
        cx = self.image.get_width() // 2
        cy = self.image.get_height() // 2
        alpha  = int(255 * (1 - self.age / self.life))
        r      = self.r
        # Outer ring
        col    = (*self.color, alpha)
        pygame.draw.circle(self.image, col,       (cx, cy), r)
        pygame.draw.circle(self.image, (*YELLOW, min(alpha, 200)), (cx, cy), max(1, r - 6))
        pygame.draw.circle(self.image, (*WHITE,  min(alpha, 160)), (cx, cy), max(1, r - 14))

    def draw(self, surf):
        surf.blit(self.image, self.rect)


# ── Screen flash ──────────────────────────────────────────────────────────
class ScreenFlash:
    def __init__(self):
        self.life  = 0
        self.color = WHITE
        self.surf  = pygame.Surface((W, H), pygame.SRCALPHA)

    def trigger(self, color=WHITE, duration=8):
        self.life  = duration
        self.color = color

    def update(self):
        if self.life > 0:
            self.life -= 1

    def draw(self, surf):
        if self.life > 0:
            alpha = int(180 * self.life / 12)
            self.surf.fill((*self.color, alpha))
            surf.blit(self.surf, (0, 0))
