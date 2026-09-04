"""
entities/effects.py
-------------------
Visual FX, Explosions, Thruster Sparks, Shockwaves, and Celestial Cosmic Bodies
(Planets with atmospheric shading & rings, glowing radiant stars).
"""
import pygame
import random
import math
from core.settings import (W, H, STAR_COUNT, YELLOW, ORANGE, RED, WHITE, BLUE, CYAN,
                            RETRO_AMBER, RETRO_TERRA, RETRO_SAGE, RETRO_CREAM, RETRO_CRIMSON, RETRO_MOSS)


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
            c = tuple(int(ch * alpha) for ch in p['color'])
            pygame.draw.circle(surf, c, (int(p['x']), int(p['y'])), p['size'])


# ── Explosion ─────────────────────────────────────────────────────────────
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, radius=40, duration=24, color=(255, 140, 30)):
        super().__init__()
        self.x = x
        self.y = y
        self.max_r = radius
        self.duration = duration
        self.timer = duration
        self.color = color
        self.particles = []
        for _ in range(int(radius * 0.8)):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(1.5, radius * 0.22)
            self.particles.append({
                'x': float(x), 'y': float(y),
                'vx': math.cos(ang) * spd,
                'vy': math.sin(ang) * spd,
                'life': random.randint(duration // 2, duration),
                'max': duration,
                'color': random.choice([YELLOW, ORANGE, RED, WHITE]),
                'size': random.randint(2, 5),
            })
        self.image = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.timer -= 1
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vx'] *= 0.91
            p['vy'] *= 0.91
            p['life'] -= 1
        if self.timer <= 0:
            self.kill()

    def draw(self, surf):
        progress = 1.0 - (self.timer / self.duration)
        cur_r = int(self.max_r * math.sin(progress * math.pi * 0.85))
        alpha = int(255 * (1.0 - progress))

        if cur_r > 2:
            s = pygame.Surface((cur_r * 2 + 4, cur_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, min(255, alpha)), (cur_r + 2, cur_r + 2), cur_r)
            pygame.draw.circle(s, (255, 255, 200, min(255, int(alpha * 1.2))), (cur_r + 2, cur_r + 2), max(1, cur_r // 2))
            surf.blit(s, (self.x - cur_r - 2, self.y - cur_r - 2))

        for p in self.particles:
            if p['life'] > 0:
                p_alpha = p['life'] / p['max']
                c = tuple(int(ch * p_alpha) for ch in p['color'])
                pygame.draw.circle(surf, c, (int(p['x']), int(p['y'])), p['size'])


# ── Shockwave Ring ────────────────────────────────────────────────────────
class Shockwave(pygame.sprite.Sprite):
    def __init__(self, x, y, max_radius=80, speed=5, color=CYAN):
        super().__init__()
        self.x = x
        self.y = y
        self.r = 4.0
        self.max_r = max_radius
        self.speed = speed
        self.color = color
        self.image = pygame.Surface((max_radius * 2 + 8, max_radius * 2 + 8), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.r += self.speed
        if self.r >= self.max_r:
            self.kill()

    def draw(self, surf):
        if self.r < 1:
            return
        alpha = int(255 * (1.0 - self.r / self.max_r))
        ir = int(self.r)
        s = pygame.Surface((ir * 2 + 6, ir * 2 + 6), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (ir + 3, ir + 3), ir, 3)
        surf.blit(s, (int(self.x) - ir - 3, int(self.y) - ir - 3))


# ── Screen Flash ──────────────────────────────────────────────────────────
class ScreenFlash:
    def __init__(self):
        self.alpha = 0
        self.color = WHITE
        self.decay = 8

    def trigger(self, color=(255, 255, 255), start_alpha=120, decay=8):
        self.color = color
        self.alpha = start_alpha
        self.decay = decay

    def update(self):
        if self.alpha > 0:
            self.alpha = max(0, self.alpha - self.decay)

    def draw(self, surf):
        if self.alpha > 0:
            flash_surf = pygame.Surface((W, H), pygame.SRCALPHA)
            flash_surf.fill((*self.color, self.alpha))
            surf.blit(flash_surf, (0, 0))


# ── Camera Shake ──────────────────────────────────────────────────────────
class CameraShake:
    def __init__(self):
        self.intensity = 0.0
        self.offset_x = 0
        self.offset_y = 0
        self._decay = 0.84

    def trigger(self, intensity=8.0, duration=20):
        """Start a camera shake.
        intensity – peak pixel displacement.
        duration  – approximate number of frames until shake subsides."""
        self.intensity = max(self.intensity, float(intensity))
        # Compute a decay multiplier so intensity reaches ~5% after `duration` frames
        # decay^duration = 0.05  =>  decay = 0.05^(1/duration)
        if duration > 0:
            self._decay = 0.05 ** (1.0 / duration)
        else:
            self._decay = 0.0

    def update(self):
        if self.intensity > 0.3:
            self.offset_x = random.uniform(-self.intensity, self.intensity)
            self.offset_y = random.uniform(-self.intensity, self.intensity)
            self.intensity *= self._decay
        else:
            self.intensity = 0.0
            self.offset_x = 0
            self.offset_y = 0

    def apply(self, surf):
        if abs(self.offset_x) > 0.5 or abs(self.offset_y) > 0.5:
            surf.scroll(int(self.offset_x), int(self.offset_y))


# ── Smoke & Spark Effects ─────────────────────────────────────────────────
class SmokePuff(pygame.sprite.Sprite):
    def __init__(self, x, y, color=(80, 80, 90), radius=6, duration=35):
        super().__init__()
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-1.5, -0.5)
        self.vy = random.uniform(-0.8, 0.8)
        self.radius = radius
        self.max_r = radius * 2.2
        self.duration = duration
        self.life = duration
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.life <= 0:
            self.kill()

    def alive(self):
        return self.life > 0

    def draw(self, surf):
        progress = 1.0 - (self.life / self.duration)
        r = int(self.radius + (self.max_r - self.radius) * progress)
        alpha = int(140 * (1.0 - progress))
        if r > 1 and alpha > 0:
            s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (r + 1, r + 1), r)
            surf.blit(s, (int(self.x) - r - 1, int(self.y) - r - 1))

SmokeParticle = SmokePuff


class ElectricSpark(pygame.sprite.Sprite):
    def __init__(self, x, y, color=CYAN, duration=15):
        super().__init__()
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-3.5, 1.5)
        self.vy = random.uniform(-2.5, 2.5)
        self.duration = duration
        self.life = duration
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.life <= 0:
            self.kill()

    def alive(self):
        return self.life > 0

    def draw(self, surf):
        alpha = max(0.0, self.life / self.duration)
        c = tuple(int(ch * alpha) for ch in self.color)
        ex = int(self.x + self.vx * 2)
        ey = int(self.y + self.vy * 2)
        pygame.draw.line(surf, c, (int(self.x), int(self.y)), (ex, ey), 2)

SparkParticle = ElectricSpark


class ThrusterParticle(pygame.sprite.Sprite):
    def __init__(self, x, y, color=None, radius=3, duration=16):
        super().__init__()
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-5.5, -2.5)
        self.vy = random.uniform(-1.0, 1.0)
        self.radius = radius
        self.max_r = max(1.0, radius * 0.4)
        self.duration = duration
        self.life = duration
        self.color = color or random.choice([(255, 200, 50), (255, 130, 30), (255, 60, 20), (255, 240, 180)])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.life <= 0:
            self.kill()

    def alive(self):
        return self.life > 0

    def draw(self, surf):
        if self.life <= 0:
            return
        progress = 1.0 - (self.life / self.duration)
        r = max(1, int(self.radius - (self.radius - self.max_r) * progress))
        alpha = int(240 * (1.0 - progress))
        s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (r + 1, r + 1), r)
        surf.blit(s, (int(self.x) - r - 1, int(self.y) - r - 1))


# ── Celestial Cosmic Body (Planets, Moons, Radiant Distant Suns) ───────────
class CelestialBody:
    """Pre-rendered atmospheric planet, ringed gas giant, or distant glowing sun."""
    def __init__(self, initial=False):
        self.reset(initial)

    def reset(self, initial=False):
        self.body_type = random.choice(['gas_giant', 'terrestrial', 'ringed_world', 'radiant_star'])
        self.x = random.uniform(0, W) if initial else float(W + random.randint(150, 450))
        self.y = random.uniform(80, H - 80)
        self.speed = random.uniform(0.12, 0.38)
        
        if self.body_type == 'gas_giant':
            self.radius = random.randint(90, 160)
            base_col = random.choice([RETRO_AMBER, RETRO_TERRA, (140, 95, 60), (160, 110, 75)])
            self._surf = self._render_gas_giant(self.radius, base_col)
        elif self.body_type == 'ringed_world':
            self.radius = random.randint(80, 130)
            base_col = random.choice([RETRO_AMBER, RETRO_CREAM, (130, 85, 55)])
            self._surf = self._render_ringed_planet(self.radius, base_col)
        elif self.body_type == 'terrestrial':
            self.radius = random.randint(60, 110)
            base_col = random.choice([RETRO_MOSS, RETRO_SAGE, RETRO_TERRA, (85, 115, 110)])
            self._surf = self._render_terrestrial(self.radius, base_col)
        else: # radiant_star
            self.radius = random.randint(70, 120)
            star_col = random.choice([RETRO_AMBER, (240, 210, 150), (255, 180, 100)])
            self._surf = self._render_radiant_star(self.radius, star_col)

    def _render_gas_giant(self, r, base_col):
        size = r * 2 + 40
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2

        # Atmospheric Outer Glow
        for dr in range(12, 0, -2):
            alpha = int(18 * (1.0 - dr / 12))
            pygame.draw.circle(surf, (*base_col, alpha), (cx, cy), r + dr)

        # Base Planet Sphere
        planet_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(planet_surf, base_col, (r, r), r)

        # Horizontal Cloud Belts / Latitude Bands
        bands = 10
        band_h = (r * 2) // bands
        for i in range(bands):
            by = i * band_h
            band_factor = 0.8 + 0.4 * math.sin(i * 1.3)
            bc = (
                max(0, min(255, int(base_col[0] * band_factor))),
                max(0, min(255, int(base_col[1] * band_factor))),
                max(0, min(255, int(base_col[2] * band_factor))),
                180
            )
            pygame.draw.rect(planet_surf, bc, (0, by, r * 2, band_h))

        # Spherical 3D Mask & Terminator Crescent Shadow
        shadow_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surf, (255, 255, 255, 255), (r, r), r)
        
        # Day / Night curved shadow
        night_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for x in range(r * 2):
            factor = (x / (r * 2))
            night_alpha = int(190 * (1.0 - factor * 0.95))
            pygame.draw.line(night_surf, (8, 12, 14, night_alpha), (x, 0), (x, r * 2))
        
        planet_surf.blit(night_surf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        
        # Mask into circle
        mask = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (r, r), r)
        planet_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        surf.blit(planet_surf, (cx - r, cy - r))
        return surf

    def _render_ringed_planet(self, r, base_col):
        pad = int(r * 1.5)
        size = r * 2 + pad * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2

        # 1. Back section of planetary ring
        ring_w = int(r * 2.6)
        ring_h = int(r * 0.55)
        ring_rect = pygame.Rect(cx - ring_w // 2, cy - ring_h // 2, ring_w, ring_h)
        ring_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.ellipse(ring_surf, (*base_col, 130), ring_rect, int(r * 0.18))
        pygame.draw.ellipse(ring_surf, (220, 200, 170, 90), ring_rect.inflate(-8, -4), 2)
        
        # Back half
        surf.blit(ring_surf, (0, 0))

        # 2. Planet sphere
        planet_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(planet_surf, base_col, (r, r), r)
        
        # Latitude shade
        for i in range(6):
            by = int(i * (r * 2 / 6))
            pygame.draw.line(planet_surf, (20, 25, 28, 70), (0, by), (r * 2, by), 4)

        # Terminator shadow
        mask = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (r, r), r)
        planet_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        surf.blit(planet_surf, (cx - r, cy - r))

        # 3. Front section of planetary ring (draw lower half over the planet)
        front_clip = pygame.Surface((size, size // 2), pygame.SRCALPHA)
        front_clip.blit(ring_surf, (0, -cy))
        surf.blit(front_clip, (0, cy))

        return surf

    def _render_terrestrial(self, r, base_col):
        size = r * 2 + 30
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2

        # Atmosphere
        for dr in range(8, 0, -2):
            pygame.draw.circle(surf, (*base_col, int(15 * (1.0 - dr / 8))), (cx, cy), r + dr)

        # Sphere
        planet = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(planet, base_col, (r, r), r)

        # Craters & continents
        for _ in range(5):
            crx = random.randint(int(r * 0.3), int(r * 1.7))
            cry = random.randint(int(r * 0.3), int(r * 1.7))
            cr_r = random.randint(int(r * 0.12), int(r * 0.28))
            pygame.draw.circle(planet, (max(0, base_col[0] - 35), max(0, base_col[1] - 35), max(0, base_col[2] - 35), 140), (crx, cry), cr_r)
            pygame.draw.circle(planet, (min(255, base_col[0] + 30), min(255, base_col[1] + 30), min(255, base_col[2] + 30), 80), (crx, cry), cr_r, 2)

        # 3D spherical mask
        mask = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (r, r), r)
        planet.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        surf.blit(planet, (cx - r, cy - r))
        return surf

    def _render_radiant_star(self, r, star_col):
        size = r * 3
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2

        # Corona Glow layers
        for dr in range(r, 0, -4):
            alpha = int(45 * (1.0 - dr / r))
            pygame.draw.circle(surf, (*star_col, alpha), (cx, cy), dr)

        # Central Bright Core
        pygame.draw.circle(surf, (255, 255, 240, 210), (cx, cy), r // 3)
        pygame.draw.circle(surf, (255, 255, 255, 245), (cx, cy), r // 6)

        # Star Diffraction Spikes
        spike_len = r * 1.3
        pygame.draw.line(surf, (*star_col, 160), (cx - spike_len, cy), (cx + spike_len, cy), 2)
        pygame.draw.line(surf, (*star_col, 160), (cx, cy - spike_len), (cx, cy + spike_len), 2)

        return surf

    def update(self):
        self.x -= self.speed
        if self.x < -self._surf.get_width():
            self.reset()

    def draw(self, surf):
        surf.blit(self._surf, (int(self.x) - self._surf.get_width() // 2, int(self.y) - self._surf.get_height() // 2))


class NebulaBackdrop:
    """Parallax Deep Space Backdrop with atmospheric planets, moons & radiant stars."""
    def __init__(self, count=3):
        self.bodies = [CelestialBody(initial=True) for _ in range(count)]

    def update(self):
        for b in self.bodies:
            b.update()

    def draw(self, surf):
        for b in self.bodies:
            b.draw(surf)
