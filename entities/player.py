import pygame
import math
import random
from core.settings import (W, H, P_LIVES, P_MAX_SHIELD, P_SHIELD_REGEN,
                            P_INVINCIBLE, P_SHOOT_RATE, P_SCROLL_VEL,
                            B_SPEED, B_DAMAGE, CYAN, BLUE, GREEN, YELLOW,
                            ORANGE, WHITE, RED, PURPLE)
from entities.bullet import PlayerBullet, Missile
from systems.loadout import SKINS_BY_ID, PARTS_BY_ID


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
        from entities.effects import ThrusterParticle, SmokeParticle, SparkParticle
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

        self._draw_lives_indicator(surf)

    def _draw_lives_indicator(self, surf):
        for i in range(self.lives):
            surf.blit(self.mini_image, (14 + i * 62, H - 42))
