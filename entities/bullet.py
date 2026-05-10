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
        self.image    = pygame.Surface((22, 6), pygame.SRCALPHA)
        # Glow core
        pygame.draw.rect(self.image, (*c, 255), (4, 1, 16, 4), border_radius=3)
        pygame.draw.rect(self.image, WHITE,     (10, 2, 8, 2), border_radius=2)
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
        self.image   = pygame.Surface((30, 10), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, ORANGE, [(0,5),(8,0),(28,5),(8,10)])
        pygame.draw.rect(self.image,   YELLOW,  (20,3,8,4),   border_radius=2)
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
        self.image  = pygame.Surface((18, 5), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (*c, 255), (0, 1, 16, 3), border_radius=2)
        pygame.draw.rect(self.image, WHITE,     (0, 1,  8, 3), border_radius=2)
        self.rect   = self.image.get_rect(midright=(x, y))

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.rect.right < -20 or not (-20 <= self.rect.y <= 1100):
            self.kill()
