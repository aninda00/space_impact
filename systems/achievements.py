"""
systems/achievements.py
------------------------
Achievement System for Space Impact — Remastered.
Tracks player progress across combat, campaign, score, and shipyard milestones,
awards bonus Credits, and triggers HUD toast notifications upon unlock.
"""

ACHIEVEMENTS = [
    {
        'id': 'first_blood',
        'title': 'First Blood',
        'desc': 'Destroy your first enemy ship',
        'reward': 100,
        'icon': '💥',
    },
    {
        'id': 'boss_slayer',
        'title': 'Boss Slayer',
        'desc': 'Defeat any sector boss',
        'reward': 300,
        'icon': '👑',
    },
    {
        'id': 'sharpshooter',
        'title': 'Precision Pilot',
        'desc': 'Achieve 75% or higher accuracy in a run',
        'reward': 500,
        'icon': '🎯',
    },
    {
        'id': 'shieldless_run',
        'title': 'Shieldless Run',
        'desc': 'Complete a sector without taking any damage',
        'reward': 600,
        'icon': '🛡️',
    },
    {
        'id': 'heavy_hitter',
        'title': 'Heavy Ordnance',
        'desc': 'Deal 10,000 total damage in a single run',
        'reward': 400,
        'icon': '🚀',
    },
    {
        'id': 'campaign_sec1',
        'title': 'Outer Belt Secure',
        'desc': 'Complete Campaign Sector 1',
        'reward': 200,
        'icon': '🛡️',
    },
    {
        'id': 'campaign_clear',
        'title': 'Humanity Endures',
        'desc': 'Complete the Campaign by defeating The Overlord',
        'reward': 1000,
        'icon': '🏆',
    },
    {
        'id': 'score_10k',
        'title': 'High Scorer',
        'desc': 'Reach 10,000 score in a single run',
        'reward': 300,
        'icon': '⭐',
    },
    {
        'id': 'score_50k',
        'title': 'Ace Pilot',
        'desc': 'Reach 50,000 score in a single run',
        'reward': 600,
        'icon': '🌟',
    },
    {
        'id': 'kill_100',
        'title': 'Fleet Destroyer',
        'desc': 'Destroy 100 total enemies across all runs',
        'reward': 400,
        'icon': '☠️',
    },
    {
        'id': 'shipyard_collector',
        'title': 'Ship Collector',
        'desc': 'Own 3 or more ship skins',
        'reward': 400,
        'icon': '🛸',
    },
    {
        'id': 'parts_master',
        'title': 'Fully Equipped',
        'desc': 'Own at least 4 custom shipyard parts',
        'reward': 500,
        'icon': '🔧',
    },
    {
        'id': 'wealthy',
        'title': 'Rich Commander',
        'desc': 'Accumulate 3,000 total Credits',
        'reward': 500,
        'icon': '💰',
    },
    {
        'id': 'boss_rush_master',
        'title': 'Arena Champion',
        'desc': 'Complete a Boss Rush mode run',
        'reward': 750,
        'icon': '⚔️',
    },
    {
        'id': 'survival_veteran',
        'title': 'Survior',
        'desc': 'Survive for 3 minutes in Survival mode',
        'reward': 500,
        'icon': '⏱️',
    },
    {
        'id': 'mouse_master',
        'title': 'Smooth Operator',
        'desc': 'Complete a wave using Direct Mouse Steering',
        'reward': 250,
        'icon': '🖱️',
    },
]

ACHIEVEMENTS_BY_ID = {a['id']: a for a in ACHIEVEMENTS}


class AchievementManager:
    """Manages tracking, unlocking, notification, and rewards for achievements."""

    def __init__(self):
        self.unlocked = set()

    def load_unlocked(self, unlocked_list):
        self.unlocked = set(unlocked_list or [])

    def check_and_unlock(self, achievement_id, game_ref=None):
        """Unlock an achievement if not already unlocked. Awards credits & toast."""
        if achievement_id in self.unlocked:
            return False
        ach = ACHIEVEMENTS_BY_ID.get(achievement_id)
        if not ach:
            return False

        self.unlocked.add(achievement_id)

        if game_ref:
            # Award reward credits
            game_ref._award_credits(ach['reward'])
            # Show toast notification
            if hasattr(game_ref, 'hud') and game_ref.hud:
                game_ref.hud.show_toast(f"ACHIEVEMENT: {ach['title']} (+{ach['reward']} CR)", 120)
            from core.audio import AudioEngine
            AudioEngine().play('upgrade')

            # Save state
            self.save_to_game(game_ref)

        return True

    def check_game_events(self, game_ref):
        """Check all criteria against current game state and stats."""
        if not game_ref or not hasattr(game_ref, 'stats'):
            return

        stats = game_ref.stats
        player = game_ref.player if hasattr(game_ref, 'player') else None

        if stats.enemies_killed >= 1:
            self.check_and_unlock('first_blood', game_ref)

        if stats.bosses_killed >= 1:
            self.check_and_unlock('boss_slayer', game_ref)

        if stats.damage_dealt >= 10000:
            self.check_and_unlock('heavy_hitter', game_ref)

        if player and player.score >= 10000:
            self.check_and_unlock('score_10k', game_ref)

        if player and player.score >= 50000:
            self.check_and_unlock('score_50k', game_ref)

        if game_ref.credits >= 3000:
            self.check_and_unlock('wealthy', game_ref)

        if len(game_ref.owned_skins) >= 3:
            self.check_and_unlock('shipyard_collector', game_ref)

        if len(game_ref.owned_parts) >= 4:
            self.check_and_unlock('parts_master', game_ref)

        if player and getattr(player, 'mouse_control', False) and game_ref.wave_mgr.wave >= 2:
            self.check_and_unlock('mouse_master', game_ref)

    def save_to_game(self, game_ref):
        """Persist unlocked achievements into game save dict."""
        try:
            data = game_ref._read_save_data()
            data['unlocked_achievements'] = sorted(self.unlocked)
            game_ref._apply_profile_to_data(data)
            game_ref._write_save_data(data)
        except Exception:
            pass
