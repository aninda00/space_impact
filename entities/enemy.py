import math
import random
from dataclasses import dataclass

import pygame

from core.settings import H, E_BASE_SPEED, WHITE, CYAN, BLUE, GREEN, YELLOW, ORANGE, RED, PURPLE, PINK
from entities.bullet import EnemyBullet


@dataclass(frozen=True)
class EnemyDef:
    id: str
    name: str
    hp: int
    score: int
    size: tuple[int, int]
    color: tuple[int, int, int]
    speed: float
    shape: str
    movement_amp: tuple[int, int] = (0, 0)
    shoot_rate: tuple[int, int] | None = None
    bullet_pattern: str = "single"


ENEMY_DEFS = {
    "scout": EnemyDef(
        id="scout", name="Scout", hp=15, score=50, size=(48, 28),
        color=(80, 220, 120), speed=E_BASE_SPEED * 1.8, shape="dart",
        movement_amp=(10, 30),
    ),
    "fighter": EnemyDef(
        id="fighter", name="Fighter", hp=35, score=100, size=(65, 42),
        color=(60, 160, 255), speed=E_BASE_SPEED, shape="fighter",
        movement_amp=(15, 45), shoot_rate=(100, 220), bullet_pattern="single",
    ),
    "bomber": EnemyDef(
        id="bomber", name="Bomber", hp=80, score=250, size=(90, 58),
        color=(220, 100, 55), speed=E_BASE_SPEED * 0.65, shape="bomber",
        movement_amp=(5, 20), shoot_rate=(120, 240), bullet_pattern="spread3",
    ),
    "elite": EnemyDef(
        id="elite", name="Elite", hp=55, score=200, size=(75, 48),
        color=(170, 60, 255), speed=E_BASE_SPEED * 1.3, shape="elite",
        movement_amp=(25, 60), shoot_rate=(80, 160), bullet_pattern="burst3",
    ),
    "interceptor": EnemyDef(
        id="interceptor", name="Interceptor", hp=70, score=320, size=(82, 42),
        color=(255, 210, 70), speed=E_BASE_SPEED * 1.7, shape="interceptor",
        movement_amp=(35, 75), shoot_rate=(70, 135), bullet_pattern="twin",
    ),
    "bulwark": EnemyDef(
        id="bulwark", name="Bulwark", hp=155, score=520, size=(104, 66),
        color=(95, 215, 205), speed=E_BASE_SPEED * 0.52, shape="bulwark",
        movement_amp=(0, 12), shoot_rate=(115, 205), bullet_pattern="wall",
    ),
    "wraith": EnemyDef(
        id="wraith", name="Wraith", hp=95, score=440, size=(88, 52),
        color=(210, 80, 255), speed=E_BASE_SPEED * 1.45, shape="wraith",
        movement_amp=(45, 95), shoot_rate=(65, 125), bullet_pattern="diagonal",
    ),
    "dreadnought": EnemyDef(
        id="dreadnought", name="Dreadnought", hp=240, score=800, size=(124, 76),
        color=(255, 75, 95), speed=E_BASE_SPEED * 0.42, shape="dreadnought",
        movement_amp=(0, 18), shoot_rate=(95, 170), bullet_pattern="heavy",
    ),
}


SECTOR_ENEMY_TABLES = {
    1: [("scout", 75), ("fighter", 25)],
    2: [("scout", 40), ("fighter", 40), ("bomber", 20)],
    3: [("scout", 25), ("fighter", 35), ("bomber", 25), ("elite", 15)],
    4: [("fighter", 35), ("bomber", 30), ("elite", 35)],
    5: [("fighter", 20), ("bomber", 30), ("elite", 50)],
    6: [("fighter", 15), ("bomber", 27), ("elite", 58)],
    7: [("bomber", 34), ("elite", 66)],
    8: [("fighter", 10), ("bomber", 26), ("elite", 64)],
    9: [("elite", 35), ("interceptor", 40), ("wraith", 25)],
    10: [("bomber", 20), ("interceptor", 25), ("bulwark", 30), ("wraith", 25)],
    11: [("elite", 20), ("bulwark", 25), ("wraith", 35), ("dreadnought", 20)],
    12: [("interceptor", 20), ("wraith", 30), ("dreadnought", 35), ("bulwark", 15)],
    13: [("wraith", 25), ("dreadnought", 45), ("bulwark", 20), ("interceptor", 10)],
}


def _shade(color, amount):
    return tuple(max(0, min(255, ch + amount)) for ch in color)


def _spawn_x():
    from core.settings import W
    return W + 10


def choose_enemy_id(sector):
    table = SECTOR_ENEMY_TABLES.get(sector, SECTOR_ENEMY_TABLES[max(SECTOR_ENEMY_TABLES)])
    total = sum(weight for _, weight in table)
    roll = random.uniform(0, total)
    upto = 0
    for enemy_id, weight in table:
        upto += weight
        if roll <= upto:
            return enemy_id
    return table[-1][0]


def create_enemy(enemy_id, speed_mult=1.0):
    return DataEnemy(ENEMY_DEFS[enemy_id], speed_mult=speed_mult)


def _draw_enemy_shape(surf, spec):
    w, h = spec.size
    c = spec.color
    dark = _shade(c, -50)

    if spec.shape == "dart":
        pygame.draw.polygon(surf, c, [(0, h // 2), (w - 10, h // 4), (w, h // 2), (w - 10, 3 * h // 4)])
        pygame.draw.rect(surf, YELLOW, (w - 8, h // 2 - 2, 8, 4), border_radius=2)
    elif spec.shape == "fighter":
        pygame.draw.polygon(surf, c, [(w - 4, h // 4 + 2), (6, h // 2), (w - 4, 3 * h // 4 - 2)])
        pygame.draw.rect(surf, c, (8, h // 4, w - 16, h // 2), border_radius=5)
        pygame.draw.polygon(surf, dark, [(15, h // 4), (35, h // 4), (30, 2), (18, 2)])
        pygame.draw.polygon(surf, dark, [(15, 3 * h // 4), (35, 3 * h // 4), (30, h - 2), (18, h - 2)])
        pygame.draw.ellipse(surf, _shade(BLUE, -70), (22, h // 2 - 7, 18, 14))
        pygame.draw.rect(surf, YELLOW, (w - 10, h // 2 - 3, 10, 6), border_radius=3)
    elif spec.shape == "bomber":
        pygame.draw.ellipse(surf, c, (4, h // 4, w - 8, h // 2))
        pygame.draw.polygon(surf, c, [(6, h // 4), (w - 4, h // 3), (w - 4, 2 * h // 3), (6, 3 * h // 4)])
        pygame.draw.polygon(surf, dark, [(10, h // 4), (50, h // 4), (45, 0), (15, 0)])
        pygame.draw.polygon(surf, dark, [(10, 3 * h // 4), (50, 3 * h // 4), (45, h), (15, h)])
        pygame.draw.rect(surf, ORANGE, (w - 12, h // 2 - 5, 12, 10), border_radius=4)
    elif spec.shape == "elite":
        pygame.draw.polygon(surf, c, [
            (0, h // 2), (20, h // 4), (w - 4, h // 3),
            (w, h // 2), (w - 4, 2 * h // 3), (20, 3 * h // 4),
        ])
        pygame.draw.ellipse(surf, _shade(PURPLE, -70), (24, h // 2 - 8, 20, 16))
        pygame.draw.polygon(surf, PINK, [(20, h // 4), (35, h // 4), (32, 0)])
        pygame.draw.polygon(surf, PINK, [(20, 3 * h // 4), (35, 3 * h // 4), (32, h)])
        pygame.draw.rect(surf, PINK, (w - 10, h // 2 - 3, 10, 6), border_radius=3)
    elif spec.shape == "interceptor":
        pygame.draw.polygon(surf, c, [(0, h // 2), (28, h // 5), (w - 8, h // 3), (w, h // 2), (w - 8, 2 * h // 3), (28, 4 * h // 5)])
        pygame.draw.polygon(surf, dark, [(18, h // 5), (48, h // 5), (40, 0), (26, 0)])
        pygame.draw.polygon(surf, dark, [(18, 4 * h // 5), (48, 4 * h // 5), (40, h), (26, h)])
        pygame.draw.ellipse(surf, ORANGE, (30, h // 2 - 7, 22, 14))
        pygame.draw.rect(surf, YELLOW, (w - 12, h // 2 - 4, 12, 8), border_radius=3)
    elif spec.shape == "bulwark":
        pygame.draw.polygon(surf, dark, [(0, h // 2), (20, h // 5), (w - 8, h // 4), (w, h // 2), (w - 8, 3 * h // 4), (20, 4 * h // 5)])
        pygame.draw.rect(surf, c, (14, h // 4, w - 24, h // 2), border_radius=8)
        for x in range(22, w - 20, 22):
            pygame.draw.rect(surf, _shade(c, -45), (x, h // 4 + 5, 14, h // 2 - 10), border_radius=3)
        pygame.draw.circle(surf, CYAN, (24, h // 2), 8)
        pygame.draw.rect(surf, CYAN, (w - 14, h // 2 - 5, 14, 10), border_radius=4)
    elif spec.shape == "wraith":
        pygame.draw.polygon(surf, (*c, 210), [(0, h // 2), (24, h // 6), (w - 10, h // 4), (w, h // 2), (w - 10, 3 * h // 4), (24, 5 * h // 6)])
        pygame.draw.polygon(surf, (*dark, 180), [(10, h // 2), (38, 0), (54, h // 3)])
        pygame.draw.polygon(surf, (*dark, 180), [(10, h // 2), (38, h), (54, 2 * h // 3)])
        pygame.draw.ellipse(surf, PINK, (30, h // 2 - 10, 24, 20))
        pygame.draw.rect(surf, PINK, (w - 12, h // 2 - 4, 12, 8), border_radius=3)
    elif spec.shape == "dreadnought":
        pygame.draw.ellipse(surf, c, (4, h // 5, w - 8, 3 * h // 5))
        pygame.draw.polygon(surf, dark, [(0, h // 2), (34, h // 6), (w - 8, h // 4), (w, h // 2), (w - 8, 3 * h // 4), (34, 5 * h // 6)])
        for yy in [h // 2 - 18, h // 2, h // 2 + 18]:
            pygame.draw.circle(surf, YELLOW, (18, yy), 5)
        pygame.draw.rect(surf, _shade(c, -60), (42, h // 2 - 18, 50, 36), border_radius=8)
        pygame.draw.rect(surf, ORANGE, (w - 16, h // 2 - 7, 16, 14), border_radius=5)
    else:
        pygame.draw.polygon(surf, c, [(w - 2, h // 4), (2, h // 2), (w - 2, 3 * h // 4)])
        pygame.draw.rect(surf, c, (4, h // 4, w - 8, h // 2), border_radius=4)
        pygame.draw.rect(surf, YELLOW, (w - 8, h // 2 - 3, 8, 6), border_radius=3)


class DataEnemy(pygame.sprite.Sprite):
    """Enemy instance built from ENEMY_DEFS data."""

    def __init__(self, spec, speed_mult=1.0):
        super().__init__()
        self.spec = spec
        self.HP = spec.hp
        self.SCORE = spec.score
        self.SPEED = spec.speed
        self.SHOOTS = spec.shoot_rate is not None
        self.SHOOT_RATE = spec.shoot_rate or (99999, 99999)
        self.SIZE = spec.size
        self.COLOR = spec.color

        scaled_hp = int(spec.hp * (0.9 + speed_mult * 0.32))
        self.hp = max(spec.hp, scaled_hp)
        self.max_hp = self.hp
        self.speed = spec.speed * speed_mult
        self.shoot_timer = random.randint(*self.SHOOT_RATE) if self.SHOOTS else 99999
        self.flash = 0

        self.image = pygame.Surface(spec.size, pygame.SRCALPHA)
        _draw_enemy_shape(self.image, spec)
        self.rect = self.image.get_rect()
        self.rect.midleft = (
            random.randint(_spawn_x(), _spawn_x() + 80),
            random.randint(20, H - self.rect.height - 20),
        )
        self.base_y = float(self.rect.y)
        self.tick = random.uniform(0, math.pi * 2)
        lo, hi = spec.movement_amp
        self.amp = random.uniform(lo, hi) if hi > 0 else 0
        self.base_image = self.image.copy()

    def update(self):
        self.tick += 0.035
        self.rect.x -= int(self.speed)
        if self.amp:
            self.rect.y = int(self.base_y + self.amp * math.sin(self.tick))
            self.rect.y = max(10, min(H - self.rect.height - 10, self.rect.y))

        if self.flash > 0:
            self.flash -= 1
            overlay = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 160))
            self.image = self.base_image.copy()
            self.image.blit(overlay, (0, 0))
        else:
            self.image = self.base_image.copy()

        if self.rect.right < -60:
            self.kill()
        if self.SHOOTS:
            self.shoot_timer -= 1

    def try_fire(self):
        if self.SHOOTS and self.shoot_timer <= 0:
            low, high = self.SHOOT_RATE
            self.shoot_timer = random.randint(max(35, low - 12), max(60, high - 18))
            return self._make_bullets()
        return []

    def _make_bullets(self):
        x, y = self.rect.left, self.rect.centery
        if self.spec.bullet_pattern == "spread3":
            return [
                EnemyBullet(x, y, vx=-5, vy=-2),
                EnemyBullet(x, y, vx=-6, vy=0),
                EnemyBullet(x, y, vx=-5, vy=2),
            ]
        if self.spec.bullet_pattern == "burst3":
            return [EnemyBullet(x, y, vx=-7 + i, vy=0) for i in range(0, -3, -1)]
        if self.spec.bullet_pattern == "twin":
            return [
                EnemyBullet(x, y - 10, vx=-8, vy=0, color=YELLOW),
                EnemyBullet(x, y + 10, vx=-8, vy=0, color=YELLOW),
            ]
        if self.spec.bullet_pattern == "wall":
            return [EnemyBullet(x, y + off, vx=-6, vy=0, color=CYAN) for off in [-18, 0, 18]]
        if self.spec.bullet_pattern == "diagonal":
            return [
                EnemyBullet(x, y, vx=-8, vy=-3, color=PINK),
                EnemyBullet(x, y, vx=-9, vy=0, color=PINK),
                EnemyBullet(x, y, vx=-8, vy=3, color=PINK),
            ]
        if self.spec.bullet_pattern == "heavy":
            return [
                EnemyBullet(x, y - 18, vx=-7, vy=-1, color=RED),
                EnemyBullet(x, y, vx=-10, vy=0, color=ORANGE),
                EnemyBullet(x, y + 18, vx=-7, vy=1, color=RED),
            ]
        return [EnemyBullet(x, y)]

    def hit(self, damage):
        self.hp -= damage
        self.flash = 6
        return self.hp <= 0

    def hp_ratio(self):
        return max(0, self.hp / self.max_hp)


def _enemy_class(enemy_id):
    class GeneratedEnemy(DataEnemy):
        def __init__(self, speed_mult=1.0):
            super().__init__(ENEMY_DEFS[enemy_id], speed_mult=speed_mult)

    spec = ENEMY_DEFS[enemy_id]
    GeneratedEnemy.__name__ = spec.name.replace(" ", "")
    GeneratedEnemy.HP = spec.hp
    GeneratedEnemy.SCORE = spec.score
    GeneratedEnemy.SIZE = spec.size
    GeneratedEnemy.COLOR = spec.color
    return GeneratedEnemy


Scout = _enemy_class("scout")
Fighter = _enemy_class("fighter")
Bomber = _enemy_class("bomber")
Elite = _enemy_class("elite")
Interceptor = _enemy_class("interceptor")
Bulwark = _enemy_class("bulwark")
Wraith = _enemy_class("wraith")
Dreadnought = _enemy_class("dreadnought")

ENEMY_CLASSES = [Scout, Fighter, Bomber, Elite, Interceptor, Bulwark, Wraith, Dreadnought]
