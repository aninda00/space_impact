import random
from core.settings import CYAN, GREEN, YELLOW, ORANGE, PURPLE, RED, PINK, BLUE, WHITE, GOLD

# ── Upgrade Definitions ───────────────────────────────────────────────────
UPGRADES = [
    {
        'id':      'rapid_fire',
        'name':    'Rapid Fire',
        'desc':    'Increases fire rate significantly',
        'detail':  '-3 frames between shots',
        'rarity':  'common',
        'color':   CYAN,
        'max':     5,
        'icon':    '⚡',
    },
    {
        'id':      'damage_boost',
        'name':    'Armor Piercer',
        'desc':    'Each bullet deals more damage',
        'detail':  '+8 damage per bullet',
        'rarity':  'common',
        'color':   ORANGE,
        'max':     6,
        'icon':    '🔥',
    },
    {
        'id':      'double_shot',
        'name':    'Twin Cannons',
        'desc':    'Fires two bullets simultaneously',
        'detail':  '2 parallel bullets per shot',
        'rarity':  'rare',
        'color':   GREEN,
        'max':     1,
        'icon':    '🔀',
    },
    {
        'id':      'triple_shot',
        'name':    'Triple Spread',
        'desc':    'Fires three bullets in a spread',
        'detail':  '3-way spread per shot',
        'rarity':  'epic',
        'color':   PURPLE,
        'max':     1,
        'icon':    '✨',
    },
    {
        'id':      'piercing',
        'name':    'Phase Rounds',
        'desc':    'Bullets pass through enemies',
        'detail':  'Hits all enemies in a line',
        'rarity':  'rare',
        'color':   BLUE,
        'max':     1,
        'icon':    '➡️',
    },
    {
        'id':      'shield_boost',
        'name':    'Shield Matrix',
        'desc':    'Increases maximum shield capacity',
        'detail':  '+40 max shield',
        'rarity':  'common',
        'color':   (60, 180, 255),
        'max':     4,
        'icon':    '🛡️',
    },
    {
        'id':      'fast_regen',
        'name':    'Nano Repair',
        'desc':    'Shield regenerates much faster',
        'detail':  '3x shield regen rate',
        'rarity':  'rare',
        'color':   GREEN,
        'max':     3,
        'icon':    '💚',
    },
    {
        'id':      'extra_life',
        'name':    'Reserve Pilot',
        'desc':    'Gain an additional life',
        'detail':  '+1 life',
        'rarity':  'epic',
        'color':   GOLD,
        'max':     3,
        'icon':    '❤️',
    },
    {
        'id':      'missile',
        'name':    'Homing Missile',
        'desc':    'Every 5th shot fires a homing missile',
        'detail':  'High-damage seeker missile',
        'rarity':  'epic',
        'color':   RED,
        'max':     1,
        'icon':    '🚀',
    },
    {
        'id':      'speed_boost',
        'name':    'Afterburner',
        'desc':    'Ship moves faster',
        'detail':  '+6 scroll speed',
        'rarity':  'common',
        'color':   YELLOW,
        'max':     4,
        'icon':    '💨',
    },
]

RARITY_WEIGHTS = {'common': 50, 'rare': 25, 'epic': 10}

RARITY_COLORS = {
    'common': (140, 145, 165),
    'rare':   (60,  155, 255),
    'epic':   (170,  60, 255),
}


class UpgradeSystem:
    def __init__(self):
        self.player_levels = {u['id']: 0 for u in UPGRADES}

    def get_available(self, count=3):
        """Return `count` random upgrades that haven't hit max level"""
        pool = [u for u in UPGRADES if self.player_levels[u['id']] < u['max']]
        if not pool:
            return []
        weights = [RARITY_WEIGHTS[u['rarity']] for u in pool]
        chosen  = []
        pool_copy   = pool[:]
        weight_copy = weights[:]
        while len(chosen) < count and pool_copy:
            total  = sum(weight_copy)
            r      = random.uniform(0, total)
            cumul  = 0
            for i, (u, w) in enumerate(zip(pool_copy, weight_copy)):
                cumul += w
                if r <= cumul:
                    chosen.append(u)
                    pool_copy.pop(i)
                    weight_copy.pop(i)
                    break
        return chosen

    def apply(self, upgrade_id, player):
        """Apply chosen upgrade to player"""
        self.player_levels[upgrade_id] += 1
        level = self.player_levels[upgrade_id]

        if upgrade_id == 'rapid_fire':
            player.shoot_rate = max(6, player.shoot_rate - 3)
        elif upgrade_id == 'damage_boost':
            player.damage += 8
        elif upgrade_id == 'double_shot':
            player.double_shot = True
        elif upgrade_id == 'triple_shot':
            player.triple_shot = True
            player.double_shot = False  # triple supersedes double
        elif upgrade_id == 'piercing':
            player.piercing = True
        elif upgrade_id == 'shield_boost':
            player.max_shield += 40
            player.shield     = min(player.shield + 40, player.max_shield)
        elif upgrade_id == 'fast_regen':
            player.shield_regen *= 3.0
        elif upgrade_id == 'extra_life':
            player.lives = min(player.lives + 1, 6)
        elif upgrade_id == 'missile':
            player.has_missile = True
        elif upgrade_id == 'speed_boost':
            player.speed += 6

    def level_of(self, upgrade_id):
        return self.player_levels[upgrade_id]
