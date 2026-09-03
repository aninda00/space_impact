"""
SaveManager — handles all save.json I/O for Space Impact.
Extracted from core/game.py to keep the Game class focused on gameplay.
"""
import json
import os

SAVE_FILE = os.path.join(os.path.dirname(__file__), "save.json")
SAVE_KEYS = (
    'state', 'game_mode', 'sector', 'wave', 'wave_kills', 'score', 'lives', 'shield',
    'max_shield', 'shoot_rate', 'damage', 'double_shot', 'triple_shot',
    'piercing', 'has_missile', 'shield_regen', 'speed', 'player_y',
    'upg_levels', 'story_timer', 'boss_warn_timer', 'wave_banner_timer',
    'mode_timer', 'next_upgrade_timer', 'time_left'
)


class SaveManager:
    """Thread-safe, error-resilient save/load utility for Space Impact."""

    def __init__(self, save_path=None):
        self._path = save_path or SAVE_FILE

    # ── Low-level I/O ─────────────────────────────────────────────────────

    def read(self):
        """Return the full save dict, or {} on any failure."""
        if not os.path.exists(self._path):
            return {}
        try:
            with open(self._path, encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def write(self, data):
        """Atomically write data dict to the save file."""
        try:
            tmp = self._path + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, self._path)
        except Exception:
            pass

    # ── High-level helpers ────────────────────────────────────────────────

    def get(self, key, default=None):
        return self.read().get(key, default)

    def set(self, key, value):
        data = self.read()
        data[key] = value
        self.write(data)

    def update(self, mapping):
        """Merge *mapping* into the save file without touching other keys."""
        data = self.read()
        data.update(mapping)
        self.write(data)

    def delete_keys(self, keys):
        """Remove a list of keys from the save file."""
        data = self.read()
        for k in keys:
            data.pop(k, None)
        self.write(data)

    def has_campaign_save(self):
        data = self.read()
        return 'sector' in data and data.get('game_mode', 'campaign') == 'campaign'

    def get_high_score(self):
        return int(self.read().get('high_score', 0))

    def save_high_score(self, score):
        self.update({'high_score': int(score)})

    def get_campaign_progress(self):
        data = self.read()
        inferred_unlocked = 1
        if data.get('game_mode', 'campaign') == 'campaign':
            inferred_unlocked = max(1, int(data.get('sector', 1)))
        inferred_completed = max(0, inferred_unlocked - 1)
        unlocked = int(data.get('campaign_unlocked_sector', inferred_unlocked))
        completed = int(data.get('campaign_completed_sector', inferred_completed))
        return unlocked, completed

    def ensure_profile_defaults(self, data, default_parts):
        """Back-fill any missing profile keys with sane defaults."""
        if 'owned_parts' not in data:
            legacy_owned = set(data.get('owned_attachments', []))
            owned_parts = set(default_parts.values())
            legacy_map = {
                'pulse_cannon': 'laser_cannon_mk2',
                'shield_array': 'shield_generator_aegis',
                'overdrive':    'plasma_core_overdrive',
                'seeker_rack':  'missile_rack_seeker',
            }
            for old, new in legacy_map.items():
                if old in legacy_owned:
                    owned_parts.add(new)
            data['owned_parts'] = sorted(owned_parts)

        if 'equipped_parts' not in data:
            equipped_parts = dict(default_parts)
            legacy_equipped = data.get('equipped_attachment')
            legacy_equip_map = {
                'pulse_cannon': ('laser_cannon', 'laser_cannon_mk2'),
                'shield_array': ('shield_generator', 'shield_generator_aegis'),
                'overdrive':    ('plasma_core', 'plasma_core_overdrive'),
                'seeker_rack':  ('missile_rack', 'missile_rack_seeker'),
            }
            if legacy_equipped in legacy_equip_map:
                cat, part = legacy_equip_map[legacy_equipped]
                equipped_parts[cat] = part
            data['equipped_parts'] = equipped_parts

        defaults = {
            'credits': 0,
            'owned_skins': ['classic'],
            'owned_parts': sorted(default_parts.values()),
            'equipped_skin': 'classic',
            'equipped_parts': dict(default_parts),
            'campaign_unlocked_sector': 1,
            'campaign_completed_sector': 0,
            'campaign_rewarded_sector': 0,
        }
        for k, v in defaults.items():
            data.setdefault(k, v)
        return data
