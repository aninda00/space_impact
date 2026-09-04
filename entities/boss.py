import pygame
import random
import math
from dataclasses import dataclass
from core.settings import (W, H, WHITE, CYAN, BLUE, GREEN, YELLOW,
                            ORANGE, RED, PURPLE, PINK, GOLD, DGREY, GREY)
from entities.bullet import EnemyBullet


from entities.boss_art import (shade as _shade,
                                draw_spines as _draw_spines,
                                draw_eye as _draw_eye,
                                draw_engine as _draw_engine)


class Boss(pygame.sprite.Sprite):
    NAME    = "Unknown"
    HP      = 2200
    SHIELD  = 1200
    SCORE   = 2000
    SIZE    = (200, 120)
    COLOR   = (100, 100, 200)
    PHASES  = 1

    def __init__(self):
        super().__init__()
        self.max_shield = float(self.SHIELD)
        self.shield     = float(self.SHIELD)
        self.max_hp  = self.HP
        self.hp      = float(self.HP)
        self.phase   = 1
        self.tick    = 0
        self.flash   = 0
        self.entry   = True           # entering from right
        self.target_x= W - self.SIZE[0] - 40
        self.attack_timer = 0
        self.pattern_idx  = 0
        self.lane_offset_y = 0
        self._build_image()
        self.rect    = self.image.get_rect(midleft=(W + self.SIZE[0], H // 2))
        self.base_image = self.image.copy()

    def _build_image(self):
        w, h = self.SIZE
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        c = self.COLOR
        dark = _shade(c, -70)
        pygame.draw.polygon(self.image, dark, [
            (0, h // 2), (26, h // 3), (70, h // 5), (w - 34, h // 4),
            (w - 4, h // 2), (w - 34, 3 * h // 4), (70, 4 * h // 5), (26, 2 * h // 3),
        ])
        pygame.draw.ellipse(self.image, c, (18, h // 5, w - 48, 3 * h // 5))
        _draw_spines(self.image, dark, w, h, [(58, 15, 26), (108, 18, 36), (158, 15, 28)], True)
        _draw_spines(self.image, dark, w, h, [(58, 15, 26), (108, 18, 36), (158, 15, 28)], False)
        _draw_eye(self.image, 62, h // 2, 18, 12, RED)
        _draw_engine(self.image, w, h, YELLOW)
        self.rect = self.image.get_rect()

    def update(self):
        self.tick += 1

        # Entry slide-in
        if self.entry:
            self.rect.x -= 6
            lane = getattr(self, 'lane_offset_y', 0)
            self.rect.centery = H // 2 + lane
            if self.rect.right <= self.target_x + self.SIZE[0]:
                self.entry = False
            return []

        # Phase check
        self._check_phase()

        # Movement
        self._move()

        # Flash
        if self.flash > 0:
            self.flash -= 1
            overlay = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 140))
            self.image = self.base_image.copy()
            self.image.blit(overlay, (0, 0))
        else:
            self.image = self.base_image.copy()

        # Attack
        self.attack_timer -= 1
        if self.attack_timer <= 0:
            bullets = self._attack()
            rate = self._attack_rate()
            if getattr(self, 'campaign_tuned', False):
                rate = int(rate * 1.25)
            self.attack_timer = rate
            return bullets

        return []

    def _move(self):
        base_y = H // 2 - self.SIZE[1] // 2 + getattr(self, 'lane_offset_y', 0)
        amp = 70 if getattr(self, 'lane_offset_y', 0) else 120
        self.rect.y = int(base_y + math.sin(self.tick * 0.025) * amp)
        self.rect.y = max(10, min(H - self.SIZE[1] - 10, self.rect.y))

    def _check_phase(self):
        pass

    def _attack(self):
        return [EnemyBullet(self.rect.left, self.rect.centery)]

    def _attack_rate(self):
        return 60

    def hit(self, damage):
        if self.shield > 0:
            self.shield = max(0.0, self.shield - damage)
        else:
            self.hp -= damage
        self.flash = 5
        return self.hp <= 0

    def hp_ratio(self):
        return max(0, self.hp / self.max_hp)

    def shield_ratio(self):
        if self.max_shield <= 0:
            return 0
        return max(0, self.shield / self.max_shield)

    def draw_healthbar(self, surf, offset_y=0):
        from core.assets import Assets
        a   = Assets()
        bw  = 600
        bh  = 22
        bx  = W // 2 - bw // 2
        shield_h = 14
        gap = 8
        total_h = bh + shield_h + gap + 72
        by  = H - total_h - 84 + offset_y
        # Background
        pygame.draw.rect(surf, (18, 22, 38), (bx - 16, by - 16, bw + 32, total_h + 24), border_radius=14)

        boss_label = a.render('small', "BOSS", WHITE)
        name_label = a.render('medium', self.NAME, WHITE)
        surf.blit(boss_label, (bx, by - 48))
        surf.blit(name_label, (bx + 72, by - 54))

        if self.max_shield > 0:
            sby = by
            pygame.draw.rect(surf, (30, 40, 70), (bx - 2, sby - 2, bw + 4, shield_h + 4), border_radius=6)
            shield_fill = int(bw * self.shield_ratio())
            if shield_fill > 0:
                pygame.draw.rect(surf, CYAN, (bx, sby, shield_fill, shield_h), border_radius=5)
            pygame.draw.rect(surf, GREY, (bx - 2, sby - 2, bw + 4, shield_h + 4), 2, border_radius=6)
            shield_label = a.render('small', "SHIELD", WHITE)
            surf.blit(shield_label, (bx, sby - shield_label.get_height() - 6))
            hp_y = sby + shield_h + gap
        else:
            hp_y = by

        # Fill
        fill = int(bw * self.hp_ratio())
        phase_colors = [RED, ORANGE, YELLOW, PINK]
        phase_color = phase_colors[min(self.phase - 1, len(phase_colors) - 1)]
        pygame.draw.rect(surf, (30, 30, 50), (bx-2, hp_y-2, bw+4, bh+4), border_radius=6)
        if fill > 0:
            pygame.draw.rect(surf, phase_color, (bx, hp_y, fill, bh), border_radius=5)
        # Border
        pygame.draw.rect(surf, GREY, (bx-2, hp_y-2, bw+4, bh+4), 2, border_radius=6)
        hp_label = a.render('small', "HULL", WHITE)
        surf.blit(hp_label, (bx, hp_y - hp_label.get_height() - 6))
        # Name
        name_gap = 10
        name_surf = a.render_fit(['medium', 'small'], self.NAME, WHITE, bw)
        surf.blit(name_surf, (W // 2 - name_surf.get_width() // 2, hp_y + bh + name_gap))


# ── Sector Bosses ─────────────────────────────────────────────────────────

class Vanguard(Boss):
    """Sector 1 — 3-way spread"""
    NAME   = "VANGUARD"
    HP     = 3200
    SHIELD = 1800
    SCORE  = 2000
    SIZE   = (200, 110)
    COLOR  = (60, 180, 255)
    PHASES = 1

    def _build_image(self):
        w, h = self.SIZE
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        c = self.COLOR
        dark = _shade(c, -80)
        mid = _shade(c, -35)
        pygame.draw.polygon(self.image, dark, [
            (4, h // 2), (34, h // 4), (76, 8), (w - 44, h // 5),
            (w - 4, h // 2), (w - 44, 4 * h // 5), (76, h - 8), (34, 3 * h // 4),
        ])
        pygame.draw.polygon(self.image, c, [
            (10, h // 2), (62, h // 4), (w - 30, h // 3),
            (w - 12, h // 2), (w - 30, 2 * h // 3), (62, 3 * h // 4),
        ])
        pygame.draw.polygon(self.image, mid, [(0, h // 2), (30, h // 2 - 22), (52, h // 2 - 8), (52, h // 2 + 8), (30, h // 2 + 22)])
        pygame.draw.polygon(self.image, CYAN, [(56, h // 4), (88, h // 4), (76, 0), (62, 0)])
        pygame.draw.polygon(self.image, CYAN, [(56, 3 * h // 4), (88, 3 * h // 4), (76, h), (62, h)])
        _draw_spines(self.image, dark, w, h, [(112, 12, 18), (145, 10, 16)], True)
        _draw_spines(self.image, dark, w, h, [(112, 12, 18), (145, 10, 16)], False)
        for x in [42, 78, 114]:
            pygame.draw.line(self.image, _shade(c, 40), (x, h // 3), (x + 42, h // 2), 3)
            pygame.draw.line(self.image, _shade(c, -55), (x, 2 * h // 3), (x + 42, h // 2), 3)
        _draw_eye(self.image, 68, h // 2, 17, 10, YELLOW)
        _draw_engine(self.image, w, h, CYAN)
        self.rect = self.image.get_rect()

    def _attack(self):
        x, y = self.rect.left, self.rect.centery
        return [
            EnemyBullet(x, y, vx=-7, vy=-3),
            EnemyBullet(x, y, vx=-8, vy=0),
            EnemyBullet(x, y, vx=-7, vy=3),
        ]

    def _attack_rate(self):
        return 55


class Phantom(Boss):
    """Sector 2 — teleports, aimed shots"""
    NAME   = "PHANTOM"
    HP     = 6800
    SHIELD = 3400
    SCORE  = 3500
    SIZE   = (220, 130)
    COLOR  = (130, 50, 230)
    PHASES = 2

    def __init__(self):
        super().__init__()
        self.teleport_timer = 200
        self.player_y = H // 2

    def _check_phase(self):
        if self.hp_ratio() < 0.5 and self.phase == 1:
            self.phase = 2

    def _build_image(self):
        w, h = self.SIZE
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        c = self.COLOR
        dark = _shade(c, -95)
        veil = (*c, 185)
        pygame.draw.polygon(self.image, dark, [
            (2, h // 2), (42, h // 4), (104, 4), (w - 52, h // 5),
            (w - 8, h // 2), (w - 52, 4 * h // 5), (104, h - 4), (42, 3 * h // 4),
        ])
        pygame.draw.ellipse(self.image, veil, (16, h // 5, w - 38, 3 * h // 5))
        pygame.draw.polygon(self.image, (*PINK, 165), [(48, h // 5), (96, h // 5), (84, 0), (38, 0)])
        pygame.draw.polygon(self.image, (*PINK, 165), [(48, 4 * h // 5), (96, 4 * h // 5), (84, h), (38, h)])
        pygame.draw.polygon(self.image, dark, [(6, h // 2), (40, h // 2 - 28), (66, h // 2 - 12), (66, h // 2 + 12), (40, h // 2 + 28)])
        for x in [72, 112, 152]:
            pygame.draw.ellipse(self.image, (*_shade(c, 35), 120), (x, h // 2 - 22, 30, 44))
        _draw_eye(self.image, 74, h // 2 - 13, 13, 9, PINK)
        _draw_eye(self.image, 74, h // 2 + 13, 13, 9, PINK)
        _draw_engine(self.image, w, h, PINK)
        self.rect = self.image.get_rect()

    def _move(self):
        self.teleport_timer -= 1
        if self.teleport_timer <= 0:
            lane = getattr(self, 'lane_offset_y', 0)
            if lane < 0:
                self.rect.y = random.randint(20, max(25, H // 2 - self.SIZE[1] - 30))
            elif lane > 0:
                self.rect.y = random.randint(H // 2 + 30, H - self.SIZE[1] - 20)
            else:
                self.rect.y = random.randint(20, H - self.SIZE[1] - 20)
            self.teleport_timer = 150 if self.phase == 1 else 90

    def _attack(self):
        x, y = self.rect.left, self.rect.centery
        if self.phase == 2:
            # Aimed + flanking
            return [
                EnemyBullet(x, y, vx=-8, vy=-2, color=PINK),
                EnemyBullet(x, y, vx=-9, vy=0,  color=PINK),
                EnemyBullet(x, y, vx=-8, vy=2,  color=PINK),
                EnemyBullet(x, y+40, vx=-7, vy=-1, color=PURPLE),
                EnemyBullet(x, y-40, vx=-7, vy=1,  color=PURPLE),
            ]
        return [
            EnemyBullet(x, y, vx=-8, vy=-2),
            EnemyBullet(x, y, vx=-8, vy=2),
        ]

    def _attack_rate(self):
        return 70 if self.phase == 1 else 45


class Leviathan(Boss):
    """Sector 3 — circular burst, 2 phases"""
    NAME   = "LEVIATHAN"
    HP     = 14500
    SHIELD = 6500
    SCORE  = 5000
    SIZE   = (260, 160)
    COLOR  = (200, 85, 40)
    PHASES = 2

    def _check_phase(self):
        if self.hp_ratio() < 0.5 and self.phase == 1:
            self.phase = 2

    def _build_image(self):
        w, h = self.SIZE
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        c = self.COLOR
        dark = _shade(c, -80)
        pygame.draw.polygon(self.image, dark, [
            (4, h // 2), (30, h // 3), (78, h // 7), (w - 48, h // 5),
            (w - 4, h // 2), (w - 48, 4 * h // 5), (78, 6 * h // 7), (30, 2 * h // 3),
        ])
        for i in range(6):
            x = 24 + i * 34
            plate_col = _shade(c, -12 if i % 2 else 18)
            pygame.draw.ellipse(self.image, plate_col, (x, h // 4 - i % 2 * 4, 78, h // 2 + i % 2 * 8))
            pygame.draw.line(self.image, dark, (x + 16, h // 4), (x + 8, 3 * h // 4), 3)
        pygame.draw.polygon(self.image, dark, [(0, h // 2), (38, h // 2 - 34), (70, h // 2 - 10), (70, h // 2 + 10), (38, h // 2 + 34)])
        for yy in [h // 2 - 20, h // 2, h // 2 + 20]:
            pygame.draw.polygon(self.image, YELLOW, [(20, yy), (42, yy - 7), (42, yy + 7)])
        pygame.draw.polygon(self.image, ORANGE, [(86, h // 7), (126, h // 7), (112, 0), (76, 0)])
        pygame.draw.polygon(self.image, ORANGE, [(86, 6 * h // 7), (126, 6 * h // 7), (112, h), (76, h)])
        _draw_spines(self.image, dark, w, h, [(145, 14, 24), (188, 12, 20)], True)
        _draw_spines(self.image, dark, w, h, [(145, 14, 24), (188, 12, 20)], False)
        _draw_eye(self.image, 92, h // 2, 20, 13, GOLD)
        _draw_engine(self.image, w, h, ORANGE)
        self.rect = self.image.get_rect()

    def _move(self):
        base_y = H // 2 - self.SIZE[1] // 2 + getattr(self, 'lane_offset_y', 0)
        amp = 75 if getattr(self, 'lane_offset_y', 0) else 150
        self.rect.x = int(self.target_x + math.sin(self.tick * 0.02) * 60)
        self.rect.y = int(base_y + math.sin(self.tick * 0.03) * amp)
        self.rect.y = max(10, min(H - self.SIZE[1] - 10, self.rect.y))

    def _attack(self):
        x, y = self.rect.left, self.rect.centery
        bullets = []
        count  = 8 if self.phase == 1 else 12
        for i in range(count):
            angle = (2 * math.pi / count) * i
            spd   = 6 if self.phase == 1 else 7
            bullets.append(EnemyBullet(x, y,
                vx=int(math.cos(angle + math.pi) * spd),
                vy=int(math.sin(angle) * spd),
                color=ORANGE))
        return bullets

    def _attack_rate(self):
        return 80 if self.phase == 1 else 50


class Nemesis(Boss):
    """Sector 4 — laser sweep + minions"""
    NAME   = "NEMESIS"
    HP     = 36000
    SHIELD = 16000
    SCORE  = 7000
    SIZE   = (290, 175)
    COLOR  = (50, 200, 130)
    PHASES = 2

    def __init__(self):
        super().__init__()
        self.laser_active  = False
        self.laser_timer   = 0
        self.laser_y       = H // 2

    def _check_phase(self):
        if self.hp_ratio() < 0.45 and self.phase == 1:
            self.phase = 2

    def _build_image(self):
        w, h = self.SIZE
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        c = self.COLOR
        dark = _shade(c, -95)
        toxic = (110, 255, 120)
        pygame.draw.polygon(self.image, dark, [
            (0, h // 2), (34, h // 4), (96, 6), (w - 58, h // 6),
            (w - 4, h // 2), (w - 58, 5 * h // 6), (96, h - 6), (34, 3 * h // 4),
        ])
        pygame.draw.polygon(self.image, c, [
            (10, h // 2), (84, h // 5), (w - 34, h // 4),
            (w - 10, h // 2), (w - 34, 3 * h // 4), (84, 4 * h // 5),
        ])
        pygame.draw.polygon(self.image, dark, [(4, h // 2), (48, h // 2 - 38), (82, h // 2 - 12), (82, h // 2 + 12), (48, h // 2 + 38)])
        for yy in [h // 2 - 28, h // 2, h // 2 + 28]:
            pygame.draw.circle(self.image, toxic, (32, yy), 7)
            pygame.draw.circle(self.image, WHITE, (30, yy - 2), 2)
        for i in range(5):
            x = 58 + i * 32
            pygame.draw.rect(self.image, _shade(c, -55), (x, h // 4 + i % 2 * 12, 56, 16), border_radius=4)
            pygame.draw.rect(self.image, _shade(c, 35), (x + 8, h // 2 + 14 - i % 2 * 10, 42, 12), border_radius=4)
        pygame.draw.polygon(self.image, toxic, [(88, h // 5), (132, h // 5), (120, 0), (82, 0)])
        pygame.draw.polygon(self.image, toxic, [(88, 4 * h // 5), (132, 4 * h // 5), (120, h), (82, h)])
        _draw_spines(self.image, dark, w, h, [(150, 16, 28), (200, 14, 22), (242, 11, 18)], True)
        _draw_spines(self.image, dark, w, h, [(150, 16, 28), (200, 14, 22), (242, 11, 18)], False)
        _draw_eye(self.image, 104, h // 2, 24, 15, toxic)
        pygame.draw.ellipse(self.image, (12, 55, 34), (132, h // 2 - 26, 70, 52))
        pygame.draw.ellipse(self.image, (*toxic, 120), (146, h // 2 - 14, 38, 28))
        _draw_engine(self.image, w, h, toxic)
        self.rect = self.image.get_rect()

    def _attack(self):
        x, y = self.rect.left, self.rect.centery
        bullets = []
        # Spread volley
        for vy in range(-3, 4):
            bullets.append(EnemyBullet(x, y, vx=-8, vy=vy, color=GREEN))
        if self.phase == 2:
            for vy in [-5, 5]:
                bullets.append(EnemyBullet(x, y, vx=-6, vy=vy, color=YELLOW))
        return bullets

    def _attack_rate(self):
        return 55 if self.phase == 1 else 35


class Overlord(Boss):
    """Sector 5 — command tyrant, 3 phases"""
    NAME   = "OVERLORD"
    HP     = 66000
    SHIELD = 26000
    SCORE  = 15000
    SIZE   = (320, 200)
    COLOR  = (220, 40, 80)
    PHASES = 3

    def __init__(self):
        super().__init__()
        self.sub_attack = 0

    def _check_phase(self):
        r = self.hp_ratio()
        if r < 0.33 and self.phase < 3:
            self.phase = 3
        elif r < 0.66 and self.phase < 2:
            self.phase = 2

    def _build_image(self):
        w, h = self.SIZE
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        c = self.COLOR
        dark = _shade(c, -105)
        blood = (255, 55, 45)
        pygame.draw.polygon(self.image, dark, [
            (0, h // 2), (34, h // 4), (108, 4), (w - 70, h // 8),
            (w - 4, h // 2), (w - 70, 7 * h // 8), (108, h - 4), (34, 3 * h // 4),
        ])
        pygame.draw.polygon(self.image, c, [
            (10, h // 2), (96, h // 7), (w - 42, h // 5),
            (w - 12, h // 2), (w - 42, 4 * h // 5), (96, 6 * h // 7),
        ])
        pygame.draw.polygon(self.image, dark, [(4, h // 2), (48, h // 2 - 50), (92, h // 2 - 18), (92, h // 2 + 18), (48, h // 2 + 50)])
        pygame.draw.polygon(self.image, GOLD, [(78, h // 7), (138, h // 7), (124, 0), (86, 0)])
        pygame.draw.polygon(self.image, GOLD, [(78, 6 * h // 7), (138, 6 * h // 7), (124, h), (86, h)])
        for i in range(6):
            x = 46 + i * 32
            yy = h // 5 + (i % 3) * h // 8
            pygame.draw.rect(self.image, dark, (x, yy, 74, 18), border_radius=5)
            pygame.draw.rect(self.image, _shade(c, 35), (x + 8, yy + 3, 48, 6), border_radius=3)
        for yy in [h // 2 - 44, h // 2, h // 2 + 44]:
            pygame.draw.circle(self.image, GOLD, (20, yy), 10)
            pygame.draw.circle(self.image, blood, (20, yy), 5)
        for yy in [h // 2 - 22, h // 2 + 22]:
            pygame.draw.polygon(self.image, YELLOW, [(42, yy), (76, yy - 9), (76, yy + 9)])
        _draw_spines(self.image, dark, w, h, [(144, 17, 36), (196, 17, 34), (246, 14, 28)], True)
        _draw_spines(self.image, dark, w, h, [(144, 17, 36), (196, 17, 34), (246, 14, 28)], False)
        _draw_eye(self.image, 112, h // 2 - 18, 21, 13, blood)
        _draw_eye(self.image, 112, h // 2 + 18, 21, 13, blood)
        pygame.draw.ellipse(self.image, (80, 5, 22), (150, h // 2 - 32, 86, 64))
        pygame.draw.ellipse(self.image, (*PINK, 120), (170, h // 2 - 18, 44, 36))
        _draw_engine(self.image, w, h, GOLD)
        self.rect = self.image.get_rect()

    def _move(self):
        base_y = H // 2 - self.SIZE[1] // 2 + getattr(self, 'lane_offset_y', 0)
        speed = 0.02 + (self.phase - 1) * 0.01
        amp   = (55 if getattr(self, 'lane_offset_y', 0) else 100) + (self.phase - 1) * 35
        self.rect.x = int(self.target_x + math.sin(self.tick * 0.015) * 80)
        self.rect.y = int(base_y + math.sin(self.tick * speed) * amp)
        self.rect.y = max(10, min(H - self.SIZE[1] - 10, self.rect.y))

    def _attack(self):
        x, y = self.rect.left, self.rect.centery
        bullets = []
        self.sub_attack = (self.sub_attack + 1) % 3

        if self.sub_attack == 0:
            # Spread fan
            for a in range(-4, 5):
                bullets.append(EnemyBullet(x, y, vx=-8, vy=a, color=RED))
        elif self.sub_attack == 1:
            # Circular burst
            count = 10 + self.phase * 2
            for i in range(count):
                angle = (2 * math.pi / count) * i
                spd   = 7
                bullets.append(EnemyBullet(x, y,
                    vx=int(math.cos(angle + math.pi) * spd),
                    vy=int(math.sin(angle) * spd),
                    color=ORANGE))
        else:
            # Triple stream
            for port_y in [y - 60, y, y + 60]:
                for vx in [-7, -9]:
                    bullets.append(EnemyBullet(x, port_y, vx=vx, vy=0, color=PINK))

        if self.phase == 3:
            # Bonus diagonal shots
            for vy in [-4, 4]:
                bullets.append(EnemyBullet(x, y, vx=-6, vy=vy, color=GOLD))

        return bullets

    def _attack_rate(self):
        return max(20, 65 - (self.phase - 1) * 15)


class VoidReaper(Boss):
    """Sector 6 — blade-shaped ambusher"""
    NAME   = "VOID REAPER"
    HP     = 82000
    SHIELD = 36000
    SCORE  = 22000
    SIZE   = (340, 210)
    COLOR  = (120, 30, 220)
    PHASES = 3

    def __init__(self):
        super().__init__()
        self.slash_side = 1

    def _check_phase(self):
        r = self.hp_ratio()
        if r < 0.30 and self.phase < 3:
            self.phase = 3
        elif r < 0.62 and self.phase < 2:
            self.phase = 2

    def _build_image(self):
        w, h = self.SIZE
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        c = self.COLOR
        dark = _shade(c, -105)
        violet = (190, 80, 255)
        pygame.draw.polygon(self.image, dark, [
            (0, h // 2), (62, h // 5), (132, 0), (w - 70, h // 6),
            (w - 6, h // 2), (w - 70, 5 * h // 6), (132, h), (62, 4 * h // 5),
        ])
        pygame.draw.polygon(self.image, c, [
            (14, h // 2), (104, h // 5), (w - 46, h // 3),
            (w - 14, h // 2), (w - 46, 2 * h // 3), (104, 4 * h // 5),
        ])
        pygame.draw.polygon(self.image, violet, [(74, h // 5), (142, h // 5), (124, 0), (84, 0)])
        pygame.draw.polygon(self.image, violet, [(74, 4 * h // 5), (142, 4 * h // 5), (124, h), (84, h)])
        for x in [82, 130, 178, 226]:
            pygame.draw.line(self.image, dark, (x, h // 4), (x + 54, 3 * h // 4), 4)
            pygame.draw.line(self.image, _shade(violet, 20), (x + 12, h // 2 - 12), (x + 64, h // 2 + 12), 3)
        _draw_eye(self.image, 116, h // 2, 25, 15, violet)
        _draw_spines(self.image, dark, w, h, [(172, 16, 38), (228, 14, 30), (280, 12, 24)], True)
        _draw_spines(self.image, dark, w, h, [(172, 16, 38), (228, 14, 30), (280, 12, 24)], False)
        _draw_engine(self.image, w, h, violet)
        self.rect = self.image.get_rect()

    def _move(self):
        base_y = H // 2 - self.SIZE[1] // 2 + getattr(self, 'lane_offset_y', 0)
        speed = 0.028 + (self.phase - 1) * 0.008
        amp = 90 if getattr(self, 'lane_offset_y', 0) else 210
        self.rect.x = int(self.target_x + math.sin(self.tick * 0.035) * (70 + self.phase * 12))
        self.rect.y = int(base_y + math.sin(self.tick * speed) * amp)
        self.rect.y = max(10, min(H - self.SIZE[1] - 10, self.rect.y))

    def _attack(self):
        x, y = self.rect.left, self.rect.centery
        bullets = [EnemyBullet(x, y + off, vx=-9, vy=off // 20, color=PURPLE)
                   for off in [-60, -30, 0, 30, 60]]
        if self.phase >= 2:
            self.slash_side *= -1
            for i in range(7):
                bullets.append(EnemyBullet(x, y - 84 + i * 28, vx=-7, vy=self.slash_side * (i - 3), color=PINK))
        if self.phase == 3:
            bullets += [
                EnemyBullet(x, y - 95, vx=-8, vy=4, color=YELLOW),
                EnemyBullet(x, y + 95, vx=-8, vy=-4, color=YELLOW),
            ]
        return bullets

    def _attack_rate(self):
        return max(18, 44 - (self.phase - 1) * 8)


class StarDevourer(Boss):
    """Sector 7 — solar parasite"""
    NAME   = "STAR DEVOURER"
    HP     = 108000
    SHIELD = 52000
    SCORE  = 30000
    SIZE   = (370, 230)
    COLOR  = (245, 110, 25)
    PHASES = 3

    def __init__(self):
        super().__init__()
        self.burst_spin = 0.0

    def _check_phase(self):
        r = self.hp_ratio()
        if r < 0.34 and self.phase < 3:
            self.phase = 3
        elif r < 0.68 and self.phase < 2:
            self.phase = 2

    def _build_image(self):
        w, h = self.SIZE
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        c = self.COLOR
        dark = _shade(c, -95)
        hot = (255, 220, 70)
        pygame.draw.polygon(self.image, dark, [
            (0, h // 2), (48, h // 4), (120, 4), (w - 82, h // 7),
            (w - 4, h // 2), (w - 82, 6 * h // 7), (120, h - 4), (48, 3 * h // 4),
        ])
        pygame.draw.ellipse(self.image, c, (26, h // 6, w - 74, 2 * h // 3))
        for x in [70, 118, 166, 214, 262]:
            pygame.draw.ellipse(self.image, _shade(c, -38), (x, h // 2 - 44, 70, 88))
        for yy in [h // 2 - 52, h // 2, h // 2 + 52]:
            pygame.draw.circle(self.image, hot, (34, yy), 11)
            pygame.draw.circle(self.image, RED, (34, yy), 5)
        pygame.draw.ellipse(self.image, (120, 30, 8), (132, h // 2 - 42, 102, 84))
        pygame.draw.ellipse(self.image, hot, (156, h // 2 - 24, 54, 48))
        _draw_spines(self.image, dark, w, h, [(116, 18, 44), (184, 18, 42), (252, 16, 34), (314, 12, 26)], True)
        _draw_spines(self.image, dark, w, h, [(116, 18, 44), (184, 18, 42), (252, 16, 34), (314, 12, 26)], False)
        _draw_eye(self.image, 104, h // 2, 22, 15, hot)
        _draw_engine(self.image, w, h, hot)
        self.rect = self.image.get_rect()

    def _move(self):
        base_y = H // 2 - self.SIZE[1] // 2 + getattr(self, 'lane_offset_y', 0)
        amp = (70 if getattr(self, 'lane_offset_y', 0) else 150) + self.phase * 20
        self.rect.x = int(self.target_x + math.sin(self.tick * 0.012) * 95)
        self.rect.y = int(base_y + math.sin(self.tick * 0.022) * amp)
        self.rect.y = max(10, min(H - self.SIZE[1] - 10, self.rect.y))

    def _attack(self):
        x, y = self.rect.left, self.rect.centery
        self.burst_spin += 0.22
        bullets = []
        count = 10 + self.phase * 2
        for i in range(count):
            angle = self.burst_spin + (2 * math.pi / count) * i
            spd = 6 + self.phase
            bullets.append(EnemyBullet(x, y,
                vx=int(math.cos(angle + math.pi) * spd),
                vy=int(math.sin(angle) * spd),
                color=GOLD))
        return bullets

    def _attack_rate(self):
        return max(24, 50 - self.phase * 8)


class EclipseCore(Boss):
    """Sector 8 — darkness pulse, bullet hell"""
    NAME   = "ECLIPSE CORE"
    HP     = 135000
    SHIELD = 65000
    SCORE  = 40000
    SIZE   = (380, 240)
    COLOR  = (40, 20, 60)
    PHASES = 3

    def _check_phase(self):
        r = self.hp_ratio()
        if r < 0.33 and self.phase < 3:
            self.phase = 3
        elif r < 0.66 and self.phase < 2:
            self.phase = 2

    def _build_image(self):
        w, h = self.SIZE
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        c = self.COLOR
        dark = (15, 6, 24)
        core = (255, 60, 120)
        pygame.draw.polygon(self.image, dark, [
            (0, h // 2), (52, h // 4), (130, 4), (w - 74, h // 6),
            (w - 4, h // 2), (w - 74, 5 * h // 6), (130, h - 4), (52, 3 * h // 4),
        ])
        pygame.draw.ellipse(self.image, c, (28, h // 6, w - 80, 2 * h // 3))
        for x in [74, 124, 174, 224, 274]:
            pygame.draw.ellipse(self.image, (65, 25, 95), (x, h // 2 - 48, 74, 96))
        for yy in [h // 2 - 58, h // 2, h // 2 + 58]:
            pygame.draw.polygon(self.image, core, [(38, yy), (74, yy - 12), (74, yy + 12)])
        _draw_spines(self.image, dark, w, h, [(128, 20, 48), (200, 20, 44), (272, 17, 36), (332, 14, 28)], True)
        _draw_spines(self.image, dark, w, h, [(128, 20, 48), (200, 20, 44), (272, 17, 36), (332, 14, 28)], False)
        _draw_eye(self.image, 128, h // 2 - 24, 23, 15, core)
        _draw_eye(self.image, 128, h // 2 + 24, 23, 15, core)
        pygame.draw.ellipse(self.image, (70, 0, 34), (184, h // 2 - 50, 118, 100))
        pygame.draw.ellipse(self.image, core, (214, h // 2 - 25, 58, 50))
        _draw_engine(self.image, w, h, GOLD)
        self.rect = self.image.get_rect()

    def _move(self):
        base_y = H // 2 - self.SIZE[1] // 2 + getattr(self, 'lane_offset_y', 0)
        amp = (65 if getattr(self, 'lane_offset_y', 0) else 140) + self.phase * 15
        speed = 0.018 + (self.phase - 1) * 0.005
        self.rect.x = int(self.target_x + math.sin(self.tick * 0.018) * 110)
        self.rect.y = int(base_y + math.sin(self.tick * speed) * amp)
        self.rect.y = max(10, min(H - self.SIZE[1] - 10, self.rect.y))

    def _attack(self):
        x, y = self.rect.left, self.rect.centery
        bullets = []
        self.sub_attack = (self.sub_attack + 1) % 4
        if self.sub_attack == 0:
            for a in range(-5, 6):
                bullets.append(EnemyBullet(x, y, vx=-9, vy=a, color=RED))
        elif self.sub_attack == 1:
            for off in [-90, -45, 0, 45, 90]:
                bullets.append(EnemyBullet(x, y + off, vx=-11, vy=0, color=PINK))
        elif self.sub_attack == 2:
            for i in range(8):
                ang = i * (math.pi / 4)
                bullets.append(EnemyBullet(x, y, vx=int(math.cos(ang) * 7), vy=int(math.sin(ang) * 7), color=PURPLE))
        else:
            bullets.append(EnemyBullet(x, y, vx=-12, vy=0, color=WHITE))
        return bullets

    def _attack_rate(self):
        return max(20, 48 - self.phase * 7)


class OblivionCore(Boss):
    """Sector 8 — final ancient machine"""
    NAME   = "OBLIVION CORE"
    HP     = 150000
    SHIELD = 80000
    SCORE  = 50000
    SIZE   = (410, 250)
    COLOR  = (210, 35, 70)
    PHASES = 4

    def __init__(self):
        super().__init__()
        self.sub_attack = 0

    def _check_phase(self):
        r = self.hp_ratio()
        if r < 0.25 and self.phase < 4:
            self.phase = 4
        elif r < 0.50 and self.phase < 3:
            self.phase = 3
        elif r < 0.75 and self.phase < 2:
            self.phase = 2

    def _build_image(self):
        w, h = self.SIZE
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        c = self.COLOR
        dark = _shade(c, -110)
        core = (255, 80, 185)
        pygame.draw.polygon(self.image, dark, [
            (0, h // 2), (44, h // 5), (122, 0), (w - 98, h // 9),
            (w - 4, h // 2), (w - 98, 8 * h // 9), (122, h), (44, 4 * h // 5),
        ])
        pygame.draw.polygon(self.image, c, [
            (12, h // 2), (112, h // 8), (w - 54, h // 4),
            (w - 12, h // 2), (w - 54, 3 * h // 4), (112, 7 * h // 8),
        ])
        pygame.draw.polygon(self.image, dark, [(4, h // 2), (58, h // 2 - 62), (112, h // 2 - 22), (112, h // 2 + 22), (58, h // 2 + 62)])
        for yy in [h // 2 - 64, h // 2 - 24, h // 2 + 24, h // 2 + 64]:
            pygame.draw.circle(self.image, GOLD, (24, yy), 10)
            pygame.draw.circle(self.image, core, (24, yy), 5)
        for i in range(7):
            x = 70 + i * 38
            pygame.draw.rect(self.image, dark, (x, h // 4 + (i % 2) * 20, 82, 20), border_radius=5)
            pygame.draw.rect(self.image, _shade(c, 45), (x + 10, h // 4 + 5 + (i % 2) * 20, 48, 6), border_radius=3)
        _draw_spines(self.image, dark, w, h, [(148, 18, 48), (214, 19, 48), (280, 17, 40), (348, 14, 30)], True)
        _draw_spines(self.image, dark, w, h, [(148, 18, 48), (214, 19, 48), (280, 17, 40), (348, 14, 30)], False)
        _draw_eye(self.image, 128, h // 2 - 24, 23, 15, core)
        _draw_eye(self.image, 128, h // 2 + 24, 23, 15, core)
        pygame.draw.ellipse(self.image, (70, 0, 34), (184, h // 2 - 50, 118, 100))
        pygame.draw.ellipse(self.image, core, (214, h // 2 - 25, 58, 50))
        _draw_engine(self.image, w, h, GOLD)
        self.rect = self.image.get_rect()

    def _move(self):
        base_y = H // 2 - self.SIZE[1] // 2 + getattr(self, 'lane_offset_y', 0)
        amp = (65 if getattr(self, 'lane_offset_y', 0) else 140) + self.phase * 15
        speed = 0.018 + (self.phase - 1) * 0.005
        self.rect.x = int(self.target_x + math.sin(self.tick * 0.018) * 110)
        self.rect.y = int(base_y + math.sin(self.tick * speed) * amp)
        self.rect.y = max(10, min(H - self.SIZE[1] - 10, self.rect.y))

    def _attack(self):
        x, y = self.rect.left, self.rect.centery
        bullets = []
        self.sub_attack = (self.sub_attack + 1) % 4
        if self.sub_attack == 0:
            for a in range(-5, 6):
                bullets.append(EnemyBullet(x, y, vx=-9, vy=a, color=RED))
        elif self.sub_attack == 1:
            for off in [-90, -45, 0, 45, 90]:
                bullets.append(EnemyBullet(x, y + off, vx=-11, vy=0, color=PINK))
        elif self.sub_attack == 2:
            count = 14 + self.phase * 2
            for i in range(count):
                angle = (2 * math.pi / count) * i + self.tick * 0.02
                bullets.append(EnemyBullet(x, y,
                    vx=int(math.cos(angle + math.pi) * 8),
                    vy=int(math.sin(angle) * 8),
                    color=ORANGE))
        else:
            for port_y in [y - 84, y - 28, y + 28, y + 84]:
                bullets.append(EnemyBullet(x, port_y, vx=-8, vy=-2, color=GOLD))
                bullets.append(EnemyBullet(x, port_y, vx=-10, vy=0, color=GOLD))
                bullets.append(EnemyBullet(x, port_y, vx=-8, vy=2, color=GOLD))
        if self.phase >= 3:
            bullets += [
                EnemyBullet(x, y - 115, vx=-7, vy=5, color=PURPLE),
                EnemyBullet(x, y + 115, vx=-7, vy=-5, color=PURPLE),
            ]
        return bullets

    def _attack_rate(self):
        return max(18, 54 - (self.phase - 1) * 8)


@dataclass(frozen=True)
class BossDef:
    id: str
    name: str
    hp: int
    shield: int
    score: int
    size: tuple[int, int]
    color: tuple[int, int, int]
    phases: int
    art: str
    movement: str
    attack: str
    attack_rate: tuple[int, int] = (60, 12)


BOSS_DEFS = [
    BossDef("vanguard", "VANGUARD", 3200, 1800, 2000, (200, 110), (60, 180, 255), 1, "blade", "sine", "spread3", (55, 0)),
    BossDef("phantom", "PHANTOM", 6800, 3400, 3500, (220, 130), (130, 50, 230), 2, "phantom", "teleport", "phantom", (70, 25)),
    BossDef("leviathan", "LEVIATHAN", 14500, 6500, 5000, (260, 160), (200, 85, 40), 2, "segmented", "drift", "ring", (80, 30)),
    BossDef("nemesis", "NEMESIS", 36000, 16000, 7000, (290, 175), (50, 200, 130), 2, "hive", "sine", "swarm", (55, 20)),
    BossDef("overlord", "OVERLORD", 66000, 26000, 15000, (320, 200), (220, 40, 80), 3, "overlord", "drift", "cycle", (65, 15)),
    BossDef("void_reaper", "VOID REAPER", 82000, 36000, 22000, (340, 210), (120, 30, 220), 3, "reaper", "blade", "blade", (44, 8)),
    BossDef("star_devourer", "STAR DEVOURER", 108000, 52000, 30000, (370, 230), (245, 110, 25), 3, "solar", "heavy", "solar", (58, 10)),
    BossDef("oblivion_core", "OBLIVION CORE", 150000, 80000, 50000, (410, 250), (210, 35, 70), 4, "core", "heavy", "oblivion", (54, 8)),
    BossDef("iron_seraph", "IRON SERAPH", 185000, 95000, 65000, (430, 260), (175, 195, 215), 4, "segmented", "drift", "cycle", (50, 8)),
    BossDef("plague_mother", "PLAGUE MOTHER", 220000, 115000, 80000, (450, 280), (70, 210, 95), 4, "hive", "heavy", "swarm", (44, 7)),
    BossDef("rift_colossus", "RIFT COLOSSUS", 270000, 140000, 100000, (470, 295), (90, 120, 255), 4, "phantom", "teleport", "phantom", (52, 8)),
    BossDef("crimson_judicator", "CRIMSON JUDICATOR", 330000, 170000, 130000, (500, 315), (235, 45, 55), 5, "overlord", "blade", "blade", (40, 5)),
    BossDef("eternity_engine", "ETERNITY ENGINE", 420000, 230000, 180000, (540, 340), (255, 150, 40), 5, "solar", "heavy", "oblivion", (46, 6)),
]


def _phase_from_ratio(ratio, phases):
    for phase in range(phases, 1, -1):
        if ratio < (phase - 1) / phases:
            return phase
    return 1


class DataBoss(Boss):
    """Boss instance generated from BOSS_DEFS data."""

    def __init__(self, spec):
        self.spec = spec
        self.NAME = spec.name
        self.HP = spec.hp
        self.SHIELD = spec.shield
        self.SCORE = spec.score
        self.SIZE = spec.size
        self.COLOR = spec.color
        self.PHASES = spec.phases
        self.sub_attack = 0
        self.slash_side = 1
        self.burst_spin = 0.0
        self.teleport_timer = 200
        super().__init__()

    def _check_phase(self):
        self.phase = max(self.phase, _phase_from_ratio(self.hp_ratio(), self.PHASES))

    def _build_image(self):
        w, h = self.SIZE
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        c = self.COLOR
        dark = _shade(c, -95)
        accent = self._accent()

        pygame.draw.polygon(self.image, dark, [
            (0, h // 2), (max(24, w // 7), h // 4), (max(70, w // 3), 4),
            (w - max(42, w // 5), h // 6), (w - 4, h // 2),
            (w - max(42, w // 5), 5 * h // 6), (max(70, w // 3), h - 4),
            (max(24, w // 7), 3 * h // 4),
        ])

        if self.spec.art in ("segmented", "solar"):
            for i in range(6):
                x = int(w * 0.09) + i * int(w * 0.13)
                pygame.draw.ellipse(self.image, _shade(c, -10 if i % 2 else 18), (x, h // 4, int(w * 0.22), h // 2))
        else:
            pygame.draw.polygon(self.image, c, [
                (10, h // 2), (int(w * 0.30), h // 6), (w - 42, h // 4),
                (w - 12, h // 2), (w - 42, 3 * h // 4), (int(w * 0.30), 5 * h // 6),
            ])

        pygame.draw.polygon(self.image, dark, [
            (4, h // 2), (int(w * 0.14), h // 2 - int(h * 0.26)),
            (int(w * 0.26), h // 2 - int(h * 0.08)),
            (int(w * 0.26), h // 2 + int(h * 0.08)),
            (int(w * 0.14), h // 2 + int(h * 0.26)),
        ])

        fin_x = int(w * 0.25)
        pygame.draw.polygon(self.image, accent, [(fin_x, h // 5), (fin_x + 44, h // 5), (fin_x + 30, 0), (fin_x - 4, 0)])
        pygame.draw.polygon(self.image, accent, [(fin_x, 4 * h // 5), (fin_x + 44, 4 * h // 5), (fin_x + 30, h), (fin_x - 4, h)])

        spines = [
            (int(w * 0.43), max(12, h // 13), max(22, h // 5)),
            (int(w * 0.60), max(12, h // 14), max(18, h // 6)),
            (int(w * 0.76), max(10, h // 16), max(14, h // 8)),
        ]
        _draw_spines(self.image, dark, w, h, spines, True)
        _draw_spines(self.image, dark, w, h, spines, False)

        for i in range(max(3, self.PHASES + 1)):
            yy = h // 2 + (i - max(3, self.PHASES + 1) // 2) * max(24, h // 6)
            pygame.draw.circle(self.image, accent, (max(18, w // 14), yy), max(5, h // 22))

        eye_x = int(w * 0.32)
        if self.PHASES >= 3:
            _draw_eye(self.image, eye_x, h // 2 - h // 12, max(14, w // 18), max(9, h // 18), accent)
            _draw_eye(self.image, eye_x, h // 2 + h // 12, max(14, w // 18), max(9, h // 18), accent)
        else:
            _draw_eye(self.image, eye_x, h // 2, max(16, w // 16), max(10, h // 15), accent)

        pygame.draw.ellipse(self.image, _shade(c, -115), (int(w * 0.45), h // 2 - h // 7, int(w * 0.25), 2 * h // 7))
        pygame.draw.ellipse(self.image, (*accent, 130), (int(w * 0.50), h // 2 - h // 12, int(w * 0.13), h // 6))
        _draw_engine(self.image, w, h, accent)
        self.rect = self.image.get_rect()

    def _accent(self):
        accents = {
            "vanguard": CYAN,
            "phantom": PINK,
            "leviathan": ORANGE,
            "nemesis": GREEN,
            "overlord": GOLD,
            "void_reaper": PURPLE,
            "star_devourer": GOLD,
            "oblivion_core": PINK,
            "iron_seraph": CYAN,
            "plague_mother": GREEN,
            "rift_colossus": BLUE,
            "crimson_judicator": RED,
            "eternity_engine": ORANGE,
        }
        return accents.get(self.spec.id, YELLOW)

    def _move(self):
        base_y = H // 2 - self.SIZE[1] // 2 + getattr(self, 'lane_offset_y', 0)
        lane = getattr(self, 'lane_offset_y', 0)
        amp_scale = 0.55 if lane else 1.0
        if self.spec.movement == "teleport":
            self.teleport_timer -= 1
            if self.teleport_timer <= 0:
                if lane < 0:
                    self.rect.y = random.randint(20, max(25, H // 2 - self.SIZE[1] - 30))
                elif lane > 0:
                    self.rect.y = random.randint(H // 2 + 30, H - self.SIZE[1] - 20)
                else:
                    self.rect.y = random.randint(20, H - self.SIZE[1] - 20)
                self.teleport_timer = max(70, 160 - self.phase * 35)
            return

        if self.spec.movement == "drift":
            self.rect.x = int(self.target_x + math.sin(self.tick * 0.016) * (54 + self.phase * 18))
            self.rect.y = int(base_y + math.sin(self.tick * 0.025) * ((110 + self.phase * 36) * amp_scale))
        elif self.spec.movement == "blade":
            self.rect.x = int(self.target_x + math.sin(self.tick * 0.035) * (70 + self.phase * 12))
            self.rect.y = int(base_y + math.sin(self.tick * 0.03) * (210 * amp_scale))
        elif self.spec.movement == "heavy":
            self.rect.x = int(self.target_x + math.sin(self.tick * 0.014) * 95)
            self.rect.y = int(base_y + math.sin(self.tick * 0.02) * ((135 + self.phase * 22) * amp_scale))
        else:
            self.rect.y = int(base_y + math.sin(self.tick * 0.025) * (120 * amp_scale))
        self.rect.y = max(10, min(H - self.SIZE[1] - 10, self.rect.y))

    def _attack(self):
        x, y = self.rect.left, self.rect.centery
        color = self._accent()
        pattern = self.spec.attack

        if pattern == "spread3":
            return [EnemyBullet(x, y, vx=-7, vy=-3), EnemyBullet(x, y, vx=-8, vy=0), EnemyBullet(x, y, vx=-7, vy=3)]
        if pattern == "phantom":
            bullets = [EnemyBullet(x, y, vx=-8, vy=-2, color=color), EnemyBullet(x, y, vx=-8, vy=2, color=color)]
            if self.phase >= 2:
                bullets += [
                    EnemyBullet(x, y, vx=-9, vy=0, color=PINK),
                    EnemyBullet(x, y + 40, vx=-7, vy=-1, color=PURPLE),
                    EnemyBullet(x, y - 40, vx=-7, vy=1, color=PURPLE),
                ]
            return bullets
        if pattern == "ring":
            return self._ring_burst(x, y, 8 if self.phase == 1 else 12, ORANGE)
        if pattern == "swarm":
            bullets = [EnemyBullet(x, y, vx=-8, vy=vy, color=GREEN) for vy in range(-3, 4)]
            if self.phase >= 2:
                bullets += [EnemyBullet(x, y, vx=-6, vy=-5, color=YELLOW), EnemyBullet(x, y, vx=-6, vy=5, color=YELLOW)]
            return bullets
        if pattern == "cycle":
            return self._cycle_attack(x, y)
        if pattern == "blade":
            return self._blade_attack(x, y)
        if pattern == "solar":
            self.burst_spin += 0.22
            bullets = self._ring_burst(x, y, 10 + self.phase * 2, ORANGE, spin=self.burst_spin)
            if self.phase >= 2:
                bullets += [EnemyBullet(x, y + off, vx=-10, vy=0, color=GOLD) for off in [-80, 0, 80]]
            return bullets
        if pattern == "oblivion":
            return self._oblivion_attack(x, y)
        return [EnemyBullet(x, y)]

    def _ring_burst(self, x, y, count, color, spin=0.0):
        bullets = []
        spd = 6 + min(self.phase, 3)
        for i in range(count):
            angle = spin + (2 * math.pi / count) * i
            bullets.append(EnemyBullet(
                x, y,
                vx=int(math.cos(angle + math.pi) * spd),
                vy=int(math.sin(angle) * spd),
                color=color,
            ))
        return bullets

    def _cycle_attack(self, x, y):
        bullets = []
        self.sub_attack = (self.sub_attack + 1) % 3
        if self.sub_attack == 0:
            bullets = [EnemyBullet(x, y, vx=-8, vy=a, color=RED) for a in range(-4, 5)]
        elif self.sub_attack == 1:
            bullets = self._ring_burst(x, y, 10 + self.phase * 2, ORANGE)
        else:
            for port_y in [y - 60, y, y + 60]:
                bullets += [EnemyBullet(x, port_y, vx=-7, vy=0, color=PINK), EnemyBullet(x, port_y, vx=-9, vy=0, color=PINK)]
        if self.phase >= 3:
            bullets += [EnemyBullet(x, y, vx=-6, vy=-4, color=GOLD), EnemyBullet(x, y, vx=-6, vy=4, color=GOLD)]
        return bullets

    def _blade_attack(self, x, y):
        bullets = [EnemyBullet(x, y + off, vx=-9, vy=off // 20, color=PURPLE) for off in [-60, -30, 0, 30, 60]]
        if self.phase >= 2:
            self.slash_side *= -1
            bullets += [EnemyBullet(x, y - 84 + i * 28, vx=-7, vy=self.slash_side * (i - 3), color=PINK) for i in range(7)]
        if self.phase >= 3:
            bullets += [EnemyBullet(x, y - 95, vx=-8, vy=4, color=YELLOW), EnemyBullet(x, y + 95, vx=-8, vy=-4, color=YELLOW)]
        return bullets

    def _oblivion_attack(self, x, y):
        self.sub_attack = (self.sub_attack + 1) % 4
        if self.sub_attack == 0:
            bullets = [EnemyBullet(x, y, vx=-9, vy=a, color=RED) for a in range(-5, 6)]
        elif self.sub_attack == 1:
            bullets = [EnemyBullet(x, y + off, vx=-11, vy=0, color=PINK) for off in [-90, -45, 0, 45, 90]]
        elif self.sub_attack == 2:
            bullets = self._ring_burst(x, y, 14 + self.phase * 2, ORANGE, spin=self.tick * 0.02)
        else:
            bullets = []
            for port_y in [y - 84, y - 28, y + 28, y + 84]:
                bullets += [
                    EnemyBullet(x, port_y, vx=-8, vy=-2, color=GOLD),
                    EnemyBullet(x, port_y, vx=-10, vy=0, color=GOLD),
                    EnemyBullet(x, port_y, vx=-8, vy=2, color=GOLD),
                ]
        if self.phase >= 3:
            bullets += [EnemyBullet(x, y - 115, vx=-7, vy=5, color=PURPLE), EnemyBullet(x, y + 115, vx=-7, vy=-5, color=PURPLE)]
        return bullets

    def _attack_rate(self):
        base, phase_drop = self.spec.attack_rate
        return max(18, base - (self.phase - 1) * phase_drop)


def _boss_class(spec):
    class GeneratedBoss(DataBoss):
        def __init__(self):
            super().__init__(spec)

    GeneratedBoss.__name__ = spec.name.title().replace(" ", "")
    GeneratedBoss.NAME = spec.name
    GeneratedBoss.HP = spec.hp
    GeneratedBoss.SHIELD = spec.shield
    GeneratedBoss.SCORE = spec.score
    GeneratedBoss.SIZE = spec.size
    GeneratedBoss.COLOR = spec.color
    GeneratedBoss.PHASES = spec.phases
    return GeneratedBoss


SECTOR_BOSSES = [_boss_class(spec) for spec in BOSS_DEFS]
BOSS_BY_ID = {spec.id: boss_cls for spec, boss_cls in zip(BOSS_DEFS, SECTOR_BOSSES)}

# Compatibility names for older imports. New bosses only need BOSS_DEFS entries.
Vanguard = BOSS_BY_ID["vanguard"]
Phantom = BOSS_BY_ID["phantom"]
Leviathan = BOSS_BY_ID["leviathan"]
Nemesis = BOSS_BY_ID["nemesis"]
Overlord = BOSS_BY_ID["overlord"]
VoidReaper = BOSS_BY_ID["void_reaper"]
StarDevourer = BOSS_BY_ID["star_devourer"]
OblivionCore = BOSS_BY_ID["oblivion_core"]
