import pygame
from core.settings import W, B_SPEED, BLUE, YELLOW, RED, ORANGE, CYAN, WHITE


class PlayerBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=None, angle_y=0, damage=None, piercing=False, color=None):
        super().__init__()
        self.damage   = damage or 10
        self.piercing = piercing
        spd           = speed or B_SPEED
        self.vx       = spd
        self.vy       = angle_y
        c             = color or CYAN
        self.image    = pygame.Surface((32, 12), pygame.SRCALPHA)
        # Outer energy aura glow
        pygame.draw.ellipse(self.image, (*c, 90), (0, 0, 32, 12))
        pygame.draw.rect(self.image, (*c, 255), (4, 3, 22, 6), border_radius=3)
        pygame.draw.rect(self.image, WHITE,     (12, 4, 12, 4), border_radius=2)
        self.rect     = self.image.get_rect(midleft=(x, y))

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.rect.left > W + 20 or self.rect.top > 1100 or self.rect.bottom < -20:
            self.kill()


class Missile(pygame.sprite.Sprite):
    """Homing missile upgrade"""
    def __init__(self, x, y):
        super().__init__()
        self.damage  = 60
        self.piercing= False
        self.target  = None
        self.vx      = 10.0
        self.vy      = 0.0
        self.image   = pygame.Surface((40, 16), pygame.SRCALPHA)
        # Propulsion glow trail
        pygame.draw.ellipse(self.image, (255, 100, 0, 120), (0, 3, 18, 10))
        pygame.draw.polygon(self.image, ORANGE, [(6, 8), (14, 2), (36, 8), (14, 14)])
        pygame.draw.rect(self.image,   YELLOW,  (26, 5, 10, 6), border_radius=3)
        pygame.draw.rect(self.image,   WHITE,   (30, 6, 5, 4), border_radius=2)
        self.rect    = self.image.get_rect(midleft=(x, y))
        self.age     = 0

    def set_target(self, enemies):
        if enemies:
            closest = min(enemies, key=lambda e: abs(e.rect.centery - self.rect.centery), default=None)
            self.target = closest

    def update(self):
        self.age += 1
        if self.target and self.target.alive():
            dy = self.target.rect.centery - self.rect.centery
            self.vy += max(-2, min(2, dy * 0.08))
        self.vy *= 0.92
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        if self.rect.left > W + 20 or not (0 <= self.rect.y <= 1100):
            self.kill()


class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, vx=-6, vy=0, color=None):
        super().__init__()
        self.damage = 15
        self.vx     = vx
        self.vy     = vy
        c           = color or RED
        self.image  = pygame.Surface((24, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (*c, 90), (0, 0, 24, 10))
        pygame.draw.rect(self.image, (*c, 255), (3, 2, 18, 6), border_radius=3)
        pygame.draw.rect(self.image, WHITE,     (3, 3, 8, 4), border_radius=2)
        self.rect   = self.image.get_rect(midright=(x, y))

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.rect.right < -20 or not (-20 <= self.rect.y <= 1100):
            self.kill()
