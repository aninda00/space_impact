import pygame
import math
import random
from core.settings import (W, H, P_LIVES, P_MAX_SHIELD, P_SHIELD_REGEN,
                            P_INVINCIBLE, P_SHOOT_RATE, P_SCROLL_VEL,
                            B_SPEED, B_DAMAGE, CYAN, BLUE, GREEN, YELLOW,
                            ORANGE, WHITE, RED, PURPLE)
from entities.bullet import PlayerBullet, Missile
from entities.effects import ThrusterParticle, SmokeParticle, SparkParticle
from systems.loadout import SKINS_BY_ID, PARTS_BY_ID, PART_CATEGORY_BY_ID, ICON_TYPES


class Player(pygame.sprite.Sprite):
    def __init__(self, skin_id='classic', part_ids=None):
        super().__init__()
        self.skin_id = skin_id
        self.part_ids = list(part_ids or [])
        self._build_image()
        self.rect       = self.image.get_rect(midleft=(80, H // 2))
        self.pos_y      = float(self.rect.y)
        self.vy         = 0.0        # scroll velocity
        self.lives      = P_LIVES
        self.max_shield = P_MAX_SHIELD
        self.shield     = float(P_MAX_SHIELD)
        self.invincible = 0
        self.shoot_timer= 0
        self.missile_cd = 0
        self.score      = 0
        self.sector     = 1
        self.thruster_particles = []
        self.damage_particles = []
        self.mouse_control = False   # set True to enable direct mouse steering

        # Upgrade state
        self.shoot_rate  = P_SHOOT_RATE
        self.damage      = B_DAMAGE
        self.speed_bonus = 0
        self.double_shot = False
        self.triple_shot = False
        self.piercing    = False
        self.has_missile = False
        self.missile_interval = 5   # fire missile every N shots
        self.shot_count  = 0
        self.shield_regen= P_SHIELD_REGEN
        self.speed       = P_SCROLL_VEL
        self.keyboard_accel = 1.35
        self.max_vy      = 18.0
        for part_id in self.part_ids:
            self.apply_part(part_id)

    def _build_image(self):
        colors = SKINS_BY_ID.get(self.skin_id, SKINS_BY_ID['classic'])['colors']
        W_S, H_S = 110, 55
        self.image = pygame.Surface((W_S, H_S), pygame.SRCALPHA)
        # Main body
        pygame.draw.polygon(self.image, colors['body'], [
            (10, 20), (85, 22), (105, 27), (85, 32), (10, 34)
        ])
        # Nose
        pygame.draw.polygon(self.image, colors['nose'], [
            (85, 22), (110, 27), (85, 32)
        ])
        # Cockpit dome
        pygame.draw.ellipse(self.image, (20, 30, 80), (38, 18, 32, 18))
        pygame.draw.ellipse(self.image, colors['glass'], (40, 19, 28, 15))
        # Top wing
        pygame.draw.polygon(self.image, colors['wing'], [
            (20, 20), (55, 20), (50, 2), (30, 2)
        ])
        # Bottom wing
        pygame.draw.polygon(self.image, colors['wing'], [
            (20, 34), (55, 34), (50, 52), (30, 52)
        ])
        # Engine glow
        pygame.draw.rect(self.image, colors['engine'], (0, 23, 14, 8), border_radius=3)
        pygame.draw.rect(self.image, colors['flare'], (2, 25, 10, 4), border_radius=2)
        
        # Draw equipped part icons
        self._draw_part_icons(colors)
        
        self.base_image = self.image.copy()
        self.mini_image = pygame.transform.scale(self.image, (55, 27))

    def set_skin(self, skin_id):
        self.skin_id = skin_id if skin_id in SKINS_BY_ID else 'classic'
        pos = self.rect.topleft if hasattr(self, 'rect') else None
        self._build_image()
        if pos:
            self.rect = self.image.get_rect(topleft=pos)
            self.pos_y = float(self.rect.y)

    def apply_part(self, part_id):
        if part_id not in PARTS_BY_ID:
            return
        stats = PARTS_BY_ID[part_id]['stats']
        if stats.get('damage_bonus'):
            self.damage += stats['damage_bonus']
        if stats.get('shield_bonus'):
            self.max_shield += stats['shield_bonus']
            self.shield = float(self.max_shield)
        if stats.get('regen_bonus'):
            self.shield_regen += stats['regen_bonus']
        if stats.get('shoot_rate_delta'):
            self.shoot_rate = max(6, self.shoot_rate + stats['shoot_rate_delta'])
        if stats.get('speed_bonus'):
            self.speed += stats['speed_bonus']
        if stats.get('missile'):
            self.has_missile = True
        if stats.get('missile_interval'):
            self.missile_interval = stats['missile_interval']
        if stats.get('double_shot'):
            self.double_shot = True
        if stats.get('triple_shot'):
            self.triple_shot = True
        if stats.get('piercing'):
            self.piercing = True

    def _draw_part_icons(self, colors):
        """Draw visual icons for equipped parts on the ship sprite."""
        for part_id in self.part_ids:
            if part_id not in PARTS_BY_ID:
                continue
            part = PARTS_BY_ID[part_id]
            category_id = part.get('category_id')
            if not category_id or category_id not in PART_CATEGORY_BY_ID:
                continue
            category = PART_CATEGORY_BY_ID[category_id]
            icon_type = category.get('icon_type')
            tier = part.get('icon_tier', 0)
            if icon_type and tier > 0:
                self._draw_icon(icon_type, tier, colors)

    def _draw_icon(self, icon_type, tier, colors):
        """Draw a specific icon type at the appropriate position on the ship."""
        # Tier colors: 1=Bronze, 2=Silver, 3=Gold
        tier_colors = {
            1: (180, 130, 50),   # Bronze
            2: (190, 190, 210),  # Silver
            3: (255, 215, 60),   # Gold
        }
        tier_glow = {
            1: (200, 150, 70),
            2: (220, 220, 240),
            3: (255, 235, 100),
        }
        tc = tier_colors.get(tier, (255, 255, 255))
        tg = tier_glow.get(tier, (255, 255, 255))

        if icon_type == 'cannon':
            # Front-mounted cannon barrels on the nose
            barrel_lengths = {1: 8, 2: 12, 3: 16}
            barrel_count = {1: 1, 2: 2, 3: 3}
            length = barrel_lengths.get(tier, 8)
            count = barrel_count.get(tier, 1)
            for i in range(count):
                offset_y = (i - (count - 1) / 2) * 4
                pygame.draw.rect(self.image, tc, (95, 27 + offset_y - 1, length, 2), border_radius=1)
                pygame.draw.rect(self.image, tg, (96, 27 + offset_y - 1, length - 2, 2), border_radius=1)
        elif icon_type == 'core':
            # Center body core glow
            radius = {1: 6, 2: 9, 3: 12}
            r = radius.get(tier, 6)
            pygame.draw.circle(self.image, tg, (55, 27), r + 2)
            pygame.draw.circle(self.image, tc, (55, 27), r)
            pygame.draw.circle(self.image, tg, (55, 27), max(1, r - 2))
        elif icon_type == 'shield':
            # Shield emitters on wing tips
            pygame.draw.arc(self.image, tg, (48, 0, 16, 16), -0.8, 0.8, 2)
            pygame.draw.arc(self.image, tg, (48, 39, 16, 16), -0.8, 0.8, 2)
            if tier >= 2:
                pygame.draw.arc(self.image, tc, (46, -2, 20, 20), -0.8, 0.8, 2)
                pygame.draw.arc(self.image, tc, (46, 37, 20, 20), -0.8, 0.8, 2)
            if tier >= 3:
                pygame.draw.arc(self.image, tg, (44, -4, 24, 24), -0.8, 0.8, 2)
                pygame.draw.arc(self.image, tg, (44, 35, 24, 24), -0.8, 0.8, 2)
        elif icon_type == 'sensor':
            # Sensor array on nose/top
            pygame.draw.polygon(self.image, tc, [(98, 27), (106, 22), (106, 32)])
            pygame.draw.polygon(self.image, tg, [(99, 27), (105, 23), (105, 31)])
            if tier >= 2:
                pygame.draw.line(self.image, tg, (95, 22), (95, 32), 2)
            if tier >= 3:
                pygame.draw.line(self.image, tc, (93, 20), (93, 34), 2)
        elif icon_type == 'thruster':
            # Enhanced engine nozzles at rear
            nozzle_count = {1: 1, 2: 2, 3: 3}
            count = nozzle_count.get(tier, 1)
            for i in range(count):
                offset_y = (i - (count - 1) / 2) * 6
                pygame.draw.ellipse(self.image, tg, (-4, 23 + offset_y - 3, 8, 6))
                pygame.draw.ellipse(self.image, tc, (-2, 23 + offset_y - 2, 4, 4))
        elif icon_type == 'armor':
            # Armor plates on body sides
            plate_heights = {1: 8, 2: 14, 3: 20}
            h = plate_heights.get(tier, 8)
            # Left side
            pygame.draw.rect(self.image, tc, (10, 27 - h // 2, 6, h), border_radius=2)
            pygame.draw.rect(self.image, tg, (11, 27 - h // 2 + 1, 4, h - 2), border_radius=1)
            # Right side
            pygame.draw.rect(self.image, tc, (94, 27 - h // 2, 6, h), border_radius=2)
            pygame.draw.rect(self.image, tg, (95, 27 - h // 2 + 1, 4, h - 2), border_radius=1)
        elif icon_type == 'missile':
            # Missile pods on wing roots
            pod_x_top, pod_x_bot = 58, 58
            pygame.draw.rect(self.image, tc, (pod_x_top, 8, 14, 10), border_radius=3)
            pygame.draw.rect(self.image, tg, (pod_x_top + 2, 10, 10, 6), border_radius=2)
            pygame.draw.rect(self.image, tc, (pod_x_bot, 37, 14, 10), border_radius=3)
            pygame.draw.rect(self.image, tg, (pod_x_bot + 2, 39, 10, 6), border_radius=2)
            if tier >= 2:
                pygame.draw.rect(self.image, tg, (pod_x_top - 2, 6, 2, 14), border_radius=1)
                pygame.draw.rect(self.image, tg, (pod_x_bot - 2, 35, 2, 14), border_radius=1)
            if tier >= 3:
                pygame.draw.rect(self.image, tc, (pod_x_top - 4, 5, 2, 16), border_radius=1)
                pygame.draw.rect(self.image, tc, (pod_x_bot - 4, 34, 2, 16), border_radius=1)
        elif icon_type == 'reactor':
            # Reactor core on lower body
            pygame.draw.ellipse(self.image, tg, (40, 34, 30, 14))
            pygame.draw.ellipse(self.image, tc, (42, 35, 26, 12))
            pygame.draw.ellipse(self.image, tg, (46, 36, 18, 10))
            if tier >= 2:
                pygame.draw.rect(self.image, tg, (38, 40, 34, 4), border_radius=2)
            if tier >= 3:
                pygame.draw.rect(self.image, tc, (36, 44, 38, 4), border_radius=2)
        elif icon_type == 'cooling':
            # Cooling vents on upper body
            vent_count = {1: 2, 2: 3, 3: 4}
            count = vent_count.get(tier, 2)
            for i in range(count):
                x = 30 + i * 12
                pygame.draw.rect(self.image, tc, (x, 8, 8, 4), border_radius=1)
                pygame.draw.rect(self.image, tg, (x + 1, 9, 6, 2), border_radius=1)
        elif icon_type == 'wing':
            # Wing tip extensions
            ext_length = {1: 6, 2: 12, 3: 18}
            ext = ext_length.get(tier, 6)
            # Top wing tip
            pygame.draw.polygon(self.image, tc, [(50, 2), (50 + ext, -2), (55 + ext, 4), (55, 2)])
            pygame.draw.polygon(self.image, tg, [(51, 2), (50 + ext, 0), (54 + ext, 3), (54, 2)])
            # Bottom wing tip
            pygame.draw.polygon(self.image, tc, [(50, 52), (50 + ext, 54), (55 + ext, 48), (55, 52)])
            pygame.draw.polygon(self.image, tg, [(51, 52), (50 + ext, 52), (54 + ext, 49), (54, 52)])

    def handle_scroll(self, dy):
        """dy: -1 scroll up, +1 scroll down"""
        self.vy += dy * (self.speed * 0.32)
        self.vy = max(-self.max_vy, min(self.max_vy, self.vy))

    def update(self, bullets_group, enemies_group):
        # Smooth vertical movement — keyboard/scroll OR direct mouse tracking
        keys = pygame.key.get_pressed()
        if self.mouse_control:
            # Direct mouse steering: lerp ship Y toward mouse cursor Y
            mx, my = pygame.mouse.get_pos()
            target_y = float(my) - self.rect.height / 2
            self.pos_y += (target_y - self.pos_y) * 0.12
            self.vy = 0.0
        else:
            up_k = getattr(self, 'up_key', pygame.K_w)
            down_k = getattr(self, 'down_key', pygame.K_s)
            move_dir = (
                keys[down_k] or keys[pygame.K_s] or keys[pygame.K_DOWN]
            ) - (
                keys[up_k] or keys[pygame.K_w] or keys[pygame.K_UP]
            )
            if move_dir:
                self.vy += move_dir * self.keyboard_accel
            self.vy = max(-self.max_vy, min(self.max_vy, self.vy))
            self.pos_y += self.vy
            self.vy *= 0.86

        min_y = 5
        max_y = H - self.rect.height - 5
        self.pos_y = max(min_y, min(max_y, self.pos_y))
        self.rect.y = int(round(self.pos_y))
        if self.rect.y in (min_y, max_y):
            self.vy = 0.0

        # Player X boundary (left half)
        self.rect.x = max(10, min(W // 2 - self.rect.width, self.rect.x))

        # Spawn thruster exhaust particles
        if random.random() < 0.8:
            self.thruster_particles.append(
                ThrusterParticle(self.rect.left + 5, self.rect.centery + random.randint(-4, 4))
            )

        # Low HP / Shield Damage trailing smoke & sparks
        if self.shield / float(self.max_shield) < 0.35 or self.lives <= 1:
            if random.random() < 0.5:
                self.damage_particles.append(
                    SmokeParticle(self.rect.left + random.randint(10, 40), self.rect.centery + random.randint(-8, 8))
                )
            if random.random() < 0.25:
                self.damage_particles.append(
                    SparkParticle(self.rect.left + random.randint(15, 50), self.rect.centery + random.randint(-6, 6))
                )

        # Timers
        if self.invincible  > 0: self.invincible  -= 1
        if self.shoot_timer > 0: self.shoot_timer  -= 1
        if self.missile_cd  > 0: self.missile_cd   -= 1

        # Shield regen (only when not recently hit)
        if self.invincible == 0 and self.shield < self.max_shield:
            self.shield = min(self.max_shield, self.shield + self.shield_regen)

        # Auto shoot
        new_bullets = []
        if self.shoot_timer == 0:
            self.shoot_timer = self.shoot_rate
            self.shot_count += 1
            new_bullets = self._fire()
        for b in new_bullets:
            bullets_group.add(b)

        # Flicker when invincible
        if self.invincible > 0 and (self.invincible // 5) % 2 == 0:
            self.image = pygame.Surface(self.base_image.get_size(), pygame.SRCALPHA)
        else:
            self.image = self.base_image.copy()
            self._apply_upgrade_glow()

    def _fire(self):
        bullets = []
        x, y = self.rect.right - 5, self.rect.centery
        from core.audio import AudioEngine
        audio = AudioEngine()

        # Missile shot
        if self.has_missile and self.shot_count % self.missile_interval == 0:
            m = Missile(x, y)
            bullets.append(m)
            audio.play('missile')

        def make(vy=0):
            return PlayerBullet(x, y, damage=self.damage,
                                piercing=self.piercing,
                                angle_y=vy)

        if self.triple_shot:
            bullets += [make(-3), make(0), make(3)]
        elif self.double_shot:
            bullets += [make(-2), make(2)]
        else:
            bullets.append(make(0))
        audio.play('laser')
        return bullets

    def _apply_upgrade_glow(self):
        if self.triple_shot:
            pygame.draw.rect(self.image, PURPLE, (0, 23, 14, 8), border_radius=3)
        elif self.double_shot:
            pygame.draw.rect(self.image, GREEN,  (0, 23, 14, 8), border_radius=3)

    def hit(self, damage=15):
        if self.invincible > 0:
            return False
        from core.audio import AudioEngine
        AudioEngine().play('hit')
        self.shield -= damage
        if self.shield <= 0:
            self.shield     = 0
            self.lives     -= 1
            self.shield     = float(self.max_shield)
            self.invincible = P_INVINCIBLE
            return True   # life lost
        self.invincible = 30  # short grace after shield hit
        return False

    def draw(self, surf):
        # Draw thruster & damage trail particles
        if hasattr(self, 'thruster_particles'):
            self.thruster_particles = [p for p in self.thruster_particles if p.alive()]
            for p in self.thruster_particles:
                p.update()
                p.draw(surf)

        if hasattr(self, 'damage_particles'):
            self.damage_particles = [p for p in self.damage_particles if p.alive()]
            for p in self.damage_particles:
                p.update()
                p.draw(surf)

        # Draw ship
        surf.blit(self.image, self.rect)

        # Draw translucent shield bubble if shield is active or hit
        if self.shield > 0 and (self.invincible > 0 or self.shield / self.max_shield > 0.2):
            s_alpha = 140 if self.invincible > 0 else int(40 + 50 * (self.shield / self.max_shield))
            shield_surf = pygame.Surface((self.rect.w + 24, self.rect.h + 20), pygame.SRCALPHA)
            pygame.draw.ellipse(shield_surf, (*CYAN, s_alpha // 3), shield_surf.get_rect())
            pygame.draw.ellipse(shield_surf, (*CYAN, s_alpha), shield_surf.get_rect(), 2)
            surf.blit(shield_surf, (self.rect.x - 12, self.rect.y - 10))

    #     self._draw_lives_indicator(surf)

    # def _draw_lives_indicator(self, surf):
    #     for i in range(self.lives):
    #         surf.blit(self.mini_image, (14 + i * 62, H - 42))
