"""
entities/coin.py
----------------
Coin pickup entity for credit collection in campaign mode.
Coins spawn at destroyed enemy positions and must be collected by the player.
Number of coins = enemy tier/level (Level 1 = 1 coin, Level 2 = 2 coins, etc.)
Each coin is worth 1 credit.
"""
import pygame
import random
import math
from core.settings import (W, H, YELLOW, ORANGE, GOLD, WHITE, CYAN)


class Coin(pygame.sprite.Sprite):
    """Coin pickup that spawns from destroyed enemies in campaign mode."""
    
    # Visual colors by tier/level
    TIER_COLORS = {
        1: YELLOW,          # Scout
        2: ORANGE,          # Fighter
        3: (255, 180, 0),   # Bomber
        4: (255, 215, 0),   # Elite - Gold
        5: (255, 160, 255), # Interceptor - Pink
        6: (95, 215, 205),  # Bulwark - Cyan
        7: (210, 80, 255),  # Wraith - Purple
        8: (255, 75, 95),   # Dreadnought - Red
        9: (255, 255, 100), # Boss - Bright gold
    }
    
    def __init__(self, x, y, tier=1, value=1):
        super().__init__()
        self.tier = tier
        self.value = value  # Each coin is worth 1 credit
        self.color = self.TIER_COLORS.get(tier, YELLOW)
        
        # Position and physics
        self.pos_x = float(x)
        self.pos_y = float(y)
        # Strong leftward velocity to reach player (at x~80 from spawn x~1920)
        self.vel_x = random.uniform(-12.0, -8.0)
        self.vel_y = 0.0  # No vertical velocity, travel straight
        self.gravity = 0.0  # No gravity - coins travel straight to player
        self.drag = 0.99  # Minimal drag for long distance travel
        
        # Animation
        self.bob_phase = random.uniform(0, math.pi * 2)
        self.bob_speed = 0.08
        self.bob_amplitude = 3.0
        self.spin_angle = 0.0
        self.spin_speed = 0.1
        self.scale = 1.0
        self.scale_target = 1.0
        self.scale_speed = 0.05
        
        # Magnetism to player
        self.magnet_range = 300
        self.magnet_strength = 1.2
        self.magnet_active = False
        
        # Lifetime
        self.lifetime = 600  # 10 seconds at 60 FPS
        self.max_lifetime = self.lifetime
        self.fade_start = 180  # Start fading at 3 seconds
        self.alive_flag = True
        
        # Spawn protection - prevent instant collection/magnetism
        self.spawn_protection = 30  # frames (0.5 seconds at 60 FPS)
        
        # Visual
        self.base_radius = 10
        self.glow_radius = 16
        self._build_image()
        
        # Collection sound trigger
        self.collected = False
    
    def _build_image(self):
        """Pre-render the coin sprite at various scales."""
        size = int(self.base_radius * 3)
        self.base_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2
        
        # Outer glow ring
        pygame.draw.circle(self.base_surf, (*self.color, 60), (cx, cy), self.glow_radius)
        # Main coin body
        pygame.draw.circle(self.base_surf, self.color, (cx, cy), self.base_radius)
        # Inner highlight
        pygame.draw.circle(self.base_surf, (255, 255, 200, 180), (cx - 2, cy - 2), self.base_radius // 2)
        # Edge shine
        pygame.draw.arc(self.base_surf, (255, 255, 255, 200), 
                       (cx - self.base_radius, cy - self.base_radius, self.base_radius * 2, self.base_radius * 2),
                       -0.5, 0.8, 2)
        
        self.image = self.base_surf.copy()
        self.rect = self.image.get_rect(center=(int(self.pos_x), int(self.pos_y)))
    
    def update(self, player=None):
        """Update coin physics, animation, and magnetism."""
        if not self.alive_flag:
            return
        
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()
            return
        
        # Physics - no gravity, coins travel straight with minimal drag
        self.vel_x *= self.drag
        self.vel_y *= self.drag
        self.pos_x += self.vel_x
        self.pos_y += self.vel_y
        
        # Bobbing animation
        self.bob_phase += self.bob_speed
        bob_offset = math.sin(self.bob_phase) * self.bob_amplitude
        
        # Spin animation
        self.spin_angle += self.spin_speed
        
        # Scale pulse
        self.scale += (self.scale_target - self.scale) * self.scale_speed
        
        # Spawn protection - prevent instant magnetism/collection
        if self.spawn_protection > 0:
            self.spawn_protection -= 1
        
        # Magnetism to player (after spawn protection)
        if player and player.alive() and self.spawn_protection <= 0:
            dx = player.rect.centerx - self.pos_x
            dy = player.rect.centery - self.pos_y
            dist = math.hypot(dx, dy)
            
            if dist < self.magnet_range:
                self.magnet_active = True
                if dist > 0:
                    force = self.magnet_strength * (1.0 - dist / self.magnet_range)
                    self.vel_x += (dx / dist) * force
                    self.vel_y += (dy / dist) * force
            else:
                self.magnet_active = False
        
        # Update rect position with bob offset
        self.rect.center = (int(self.pos_x), int(self.pos_y + bob_offset))
        
        # Fade out near end of lifetime
        if self.lifetime < self.fade_start:
            alpha = int(255 * (self.lifetime / self.fade_start))
            self.image = self.base_surf.copy()
            self.image.set_alpha(alpha)
        else:
            self.image = self.base_surf.copy()
        
        # Apply spin by rotating (simplified - just visual scale pulse for now)
        # Full rotation would require re-rendering each frame which is expensive
        # Instead we'll pulse the scale
        self.scale_target = 1.0 + 0.15 * math.sin(self.spin_angle * 2)
    
    def draw(self, surf, camera_offset=(0, 0)):
        """Draw the coin with camera offset."""
        if not self.alive_flag:
            return
        
        # Apply camera offset
        draw_x = self.rect.x - camera_offset[0]
        draw_y = self.rect.y - camera_offset[1]
        
        # Draw glow when magnet active
        if self.magnet_active and self.lifetime > self.fade_start:
            pulse = (math.sin(self.spin_angle * 4) + 1) * 0.5
            glow_size = int(self.glow_radius * (1.0 + pulse * 0.3))
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color, int(80 + pulse * 60)), 
                              (glow_size, glow_size), glow_size)
            surf.blit(glow_surf, (draw_x + self.rect.width // 2 - glow_size, 
                                  draw_y + self.rect.height // 2 - glow_size))
        
        # Draw main coin
        surf.blit(self.image, (draw_x, draw_y))
        
        # Draw value indicator when magnet active
        if self.magnet_active and self.lifetime > self.fade_start:
            font = pygame.font.Font(None, 18)
            value_text = font.render(f"+{self.value}", True, (255, 255, 200))
            text_rect = value_text.get_rect(center=(draw_x + self.rect.width // 2, 
                                                    draw_y - 10))
            surf.blit(value_text, text_rect)
    
    def collect(self):
        """Mark coin as collected."""
        self.alive_flag = False
        self.collected = True
        self.kill()
    
    @classmethod
    def create_for_enemy(cls, x, y, enemy):
        """Create coins appropriate for the given enemy.
        Number of coins = enemy tier level (Level 1 = 1 coin, Level 2 = 2 coins, etc.)
        Each coin is worth 1 credit.
        """
        # Determine tier from enemy (DataEnemy has spec.id, GeneratedEnemy has id)
        enemy_id = getattr(enemy, 'id', None)
        if enemy_id is None:
            enemy_id = getattr(enemy, 'spec', None)
            if enemy_id is not None:
                enemy_id = getattr(enemy.spec, 'id', 'fighter')
            else:
                enemy_id = 'fighter'
        enemy_name = getattr(enemy, 'NAME', '').lower()
        
        # Map enemy types to tier levels (1-8 for regular enemies, 9 for boss)
        if 'boss' in enemy_id or 'boss' in enemy_name:
            tier = 9  # Boss = 9 coins
        elif enemy_id in ('dreadnought',):
            tier = 8
        elif enemy_id in ('wraith',):
            tier = 7
        elif enemy_id in ('bulwark',):
            tier = 6
        elif enemy_id in ('interceptor',):
            tier = 5
        elif enemy_id in ('elite',):
            tier = 4
        elif enemy_id in ('bomber',):
            tier = 3
        elif enemy_id in ('fighter',):
            tier = 2
        elif enemy_id in ('scout', 'drone'):
            tier = 1
        else:
            tier = 1
        
        # Create multiple coins based on tier level
        coins = []
        for i in range(tier):
            # Spread coins in a small arc
            angle = (i / max(1, tier - 1)) * math.pi if tier > 1 else 0
            if tier == 1:
                offset_x = 0
                offset_y = 0
            else:
                offset_x = math.cos(angle - math.pi/2) * 15
                offset_y = math.sin(angle - math.pi/2) * 15
            
            coin = cls(x + offset_x, y + offset_y, tier, 1)  # Each coin = 1 credit
            # ADD arc velocity to the strong leftward velocity from __init__
            coin.vel_x += math.cos(angle - math.pi/2) * 1.5 + random.uniform(-0.5, 0.5)
            coin.vel_y += math.sin(angle - math.pi/2) * 1.5 - 2 + random.uniform(-0.5, 0.5)
            coins.append(coin)
        
        return coins
    
    @classmethod
    def create_for_boss(cls, x, y, boss):
        """Create a larger coin cluster for boss (9 coins for boss tier)."""
        return cls.create_for_enemy(x, y, boss)


class CoinManager:
    """Manages coin spawning and collection."""
    
    def __init__(self):
        self.coins = pygame.sprite.Group()
    
    def spawn_coin(self, x, y, enemy):
        """Spawn coin(s) for a destroyed enemy."""
        coins = Coin.create_for_enemy(x, y, enemy)
        for coin in coins:
            self.coins.add(coin)
    
    def update(self, player=None):
        """Update all coins."""
        for coin in self.coins:
            coin.update(player)
    
    def draw(self, surf, camera_offset=(0, 0)):
        """Draw all coins."""
        for coin in self.coins:
            coin.draw(surf, camera_offset)
    
    def check_collection(self, player):
        """Check for coin collection by player. Returns total value collected."""
        collected_value = 0
        for coin in self.coins:
            if coin.alive_flag and coin.spawn_protection <= 0 and coin.rect.colliderect(player.rect.inflate(20, 20)):
                coin.collect()
                collected_value += coin.value
        return collected_value
    
    def clear(self):
        """Clear all coins."""
        self.coins.empty()