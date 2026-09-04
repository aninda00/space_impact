import pygame
import sys
import math
import json
import os
from enum import Enum, auto
from core.save_manager import SaveManager, SAVE_KEYS

from core.settings import (W, H, FPS, TOTAL_SECTORS, BG, DARK, CYAN, WHITE,
                            GREY, RED, YELLOW, GREEN, ORANGE, PURPLE, BLUE, GOLD,
                            RETRO_AMBER, RETRO_TERRA, RETRO_SAGE, RETRO_CREAM, RETRO_CRIMSON, RETRO_MOSS)
from core.assets import Assets

from entities.player   import Player
from entities.effects  import StarField, Explosion, Particle, ScreenFlash, CameraShake, NebulaBackdrop
from entities.bullet   import Missile

from systems.wave_manager   import WaveManager
from systems.upgrade_system import UpgradeSystem
from systems.story          import SECTOR_STORIES, WIN_TEXT
from systems.loadout        import (SKINS_BY_ID, PARTS_BY_ID, DEFAULT_EQUIPPED_PARTS,
                                    campaign_power, recommended_power)
from systems.stats_tracker  import StatsTracker
from systems.achievements   import AchievementManager

from ui.hud            import HUD
from ui.menu           import MainMenu
from ui.upgrade_screen import UpgradeScreen
from ui.settings_screen import SettingsScreen
from ui.codex_screen    import CodexScreen
from ui.components     import Button, Panel



class State(Enum):
    MENU        = auto()
    STORY       = auto()
    PLAYING     = auto()
    BOSS_WARN   = auto()
    UPGRADE     = auto()
    SECTOR_CLEAR= auto()
    GAME_OVER   = auto()
    WIN         = auto()
    PAUSED      = auto()
    SETTINGS    = auto()
    CODEX       = auto()


class Game:
    def __init__(self, screen):
        self.screen  = screen
        self.clock   = pygame.time.Clock()
        a            = Assets()
        a.load()

        self.saver      = SaveManager()
        self.high_score = self._load_hs()
        self.starfield  = StarField()
        self.nebula     = NebulaBackdrop()
        self.menu       = MainMenu()
        self.menu.set_starfield(self.starfield)
        self.flash      = ScreenFlash()
        self.camera_shake = CameraShake()
        self.state      = State.MENU
        self.game_mode  = 'campaign'
        self._start_sector = 1
        self.credits    = 0
        self.owned_skins = {'classic'}
        self.owned_parts = set(DEFAULT_EQUIPPED_PARTS.values())
        self.equipped_skin = 'classic'
        self.equipped_parts = dict(DEFAULT_EQUIPPED_PARTS)
        self._load_profile()
        self.tick       = 0

        self._story_timer   = 0
        self._banner_timer  = 0
        self._boss_warn_timer = 0
        self._sector_clear_timer = 0
        self._last_campaign_reward = 0
        self._continue_btn  = Button(W // 2 - 160, H // 2 + 160, 320, 60,
                                     "NEXT LEVEL", color=(30, 120, 255))
        self._sector_menu_btn = Button(W // 2 - 160, H // 2 + 225, 320, 55,
                                       "CAMPAIGN MENU", color=(40, 40, 80))
        self._restart_btn   = Button(W // 2 - 160, H // 2 + 80,  320, 60,
                                     "TRY AGAIN",  color=(140, 30, 30))
        self._menu_btn      = Button(W // 2 - 160, H // 2 + 155, 320, 55,
                                     "MAIN MENU",  color=(40, 40, 80))
        self._win_restart_btn  = Button(W // 2 - 160, H - 180, 320, 60,
                                        "PLAY AGAIN", color=(30, 120, 255))
        self._win_menu_btn     = Button(W // 2 - 160, H - 105, 320, 55,
                                        "MAIN MENU",  color=(40, 40, 80))
        self._pause_button = Button(W - 135, 16, 110, 84, "PAUSE",
                                    color=(172, 80, 69), font_key='small')
        self._pause_resume_btn = Button(W // 2 - 180, H // 2 - 50,  360, 48,
                                        "RESUME",      color=(101, 135, 97))
        self._pause_settings_btn = Button(W // 2 - 180, H // 2 + 10,  360, 48,
                                          "SETTINGS & OPTIONS", color=(78, 104, 81), font_key='small')
        self._pause_save_btn   = Button(W // 2 - 180, H // 2 + 70,  360, 48,
                                        "SAVE & QUIT TO MENU", color=(101, 135, 97), font_key='small')
        self._pause_quit_btn   = Button(W // 2 - 180, H // 2 + 130, 360, 48,
                                        "QUIT GAME",   color=(184, 58, 45), font_key='small')

        self.settings_screen = SettingsScreen()
        self.codex_screen    = CodexScreen()
        self.achievements_mgr = AchievementManager()
        self._previous_state = State.MENU
        self._load_settings()

        self._init_play_objects()

    # ── Init / Reset ──────────────────────────────────────────────────────

    def _init_play_objects(self, mode=None):
        if mode:
            self.game_mode = mode
        if self.game_mode == 'campaign':
            self.player = Player(self.equipped_skin, list(self.equipped_parts.values()))
        else:
            self.player = Player(self.equipped_skin, [])
        self.wave_mgr    = WaveManager(self.game_mode)
        self.upgrade_sys = UpgradeSystem()
        self.hud         = HUD()
        self.upg_screen  = UpgradeScreen()
        self.stats       = StatsTracker()

        self.all_sprites  = pygame.sprite.Group()
        self.enemies      = pygame.sprite.Group()
        self.bullets      = pygame.sprite.Group()
        self.e_bullets    = pygame.sprite.Group()
        self.explosions   = pygame.sprite.Group()
        self.particles    = []     # Particle objects (manual draw)

        self.all_sprites.add(self.player)
        self._pending_upgrades = []
        self._boss_ref         = None
        self._wave_banner_timer = 0

        if hasattr(self, 'settings_screen'):
            if self.settings_screen.current_scheme == 'mouse':
                self.player.mouse_control = True
            elif self.settings_screen.current_scheme == 'keyboard':
                self.player.mouse_control = False
            kb = self.settings_screen.keybinds
            self.player.up_key = kb.get('up', pygame.K_w)
            self.player.down_key = kb.get('down', pygame.K_s)

    def _start_game(self, mode='campaign', sector=1):
        self._clear_progress()
        self.game_mode = mode
        self._start_sector = max(1, min(TOTAL_SECTORS, int(sector or 1)))
        self._init_play_objects(mode)
        self.stats.reset()   # fresh stats for each run
        self._boss_ref2 = None
        # Apply difficulty preset from menu
        difficulty = getattr(self.menu, '_difficulty', 'standard')
        self.wave_mgr.set_difficulty(difficulty)
        self.wave_mgr.sector = self._start_sector
        self.state = State.STORY if self.game_mode == 'campaign' else State.PLAYING
        self._story_timer = 0
        if self.game_mode == 'endless':
            self.wave_mgr.start_next_wave()
            self._wave_banner_timer = 90
        elif self.game_mode == 'boss_rush':
            self.wave_mgr.start_boss_rush()
            self.state = State.BOSS_WARN
            self._boss_warn_timer = 0
            from core.audio import AudioEngine
            AudioEngine().play('boss_warn')
        elif self.game_mode == 'survival':
            self.wave_mgr.start_survival()
            self._wave_banner_timer = 90
        elif self.game_mode == 'time_attack':
            self.wave_mgr.start_time_attack()
            self._wave_banner_timer = 90

    # ── Main Loop ─────────────────────────────────────────────────────────

    def run(self):
        canvas = pygame.Surface((W, H))
        while True:
            dt = self.clock.tick(FPS)
            self.tick += 1
            self._handle_events()
            self._update()
            self._draw(canvas)
            self.camera_shake.apply(canvas)
            win = pygame.display.get_surface()
            pygame.transform.smoothscale(canvas, win.get_size(), win)
            pygame.display.flip()

    # ── Events ────────────────────────────────────────────────────────────

    def _scale_mouse(self, pos):
        """Convert window mouse pos to internal canvas coords"""
        win = pygame.display.get_surface()
        ww, wh = win.get_size()
        sx = W / ww
        sy = H / wh
        return (int(pos[0] * sx), int(pos[1] * sy))

    def _handle_events(self):
        raw_events = pygame.event.get()
        for event in raw_events:
            if event.type == pygame.QUIT:
                if self._can_resume_current_run():
                    self._save_progress()
                self._save_hs()
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                pause_k = self.settings_screen.keybinds.get('pause', pygame.K_ESCAPE) if hasattr(self, 'settings_screen') else pygame.K_ESCAPE
                m_k     = self.settings_screen.keybinds.get('mouse_toggle', pygame.K_m) if hasattr(self, 'settings_screen') else pygame.K_m

                if event.key in (pygame.K_ESCAPE, pause_k):
                    if self.state in (State.PLAYING, State.BOSS_WARN):
                        self.state = State.PAUSED
                        continue
                    elif self.state == State.PAUSED:
                        self.state = State.PLAYING
                        continue
                    elif self.state == State.SETTINGS:
                        self.state = self._previous_state
                        continue
                    elif self.state == State.MENU:
                        pygame.quit(); sys.exit()
                if event.key == pygame.K_F5 and self.state in (State.PLAYING, State.BOSS_WARN):
                    self._save_progress()
                if event.key in (pygame.K_m, m_k) and self.state in (State.PLAYING, State.BOSS_WARN):
                    self.player.mouse_control = not self.player.mouse_control
                    label = "Mouse" if self.player.mouse_control else "Keyboard"
                    self.hud.show_toast(f"{label} controls")

            # Mouse scroll for player movement
            if event.type == pygame.MOUSEWHEEL and self.state == State.PLAYING:
                self.player.handle_scroll(-event.y)

            # Scale mouse pos to internal canvas coords for all click/move events
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                sp = self._scale_mouse(event.pos)
                event = pygame.event.Event(event.type, button=getattr(event,'button',1), pos=sp)

            # Menu
            if self.state == State.MENU:
                result = self.menu.handle_event(event)
                if result == 'play':
                    self._start_game('campaign', 1)
                elif result == 'endless':
                    self._start_game('endless')
                elif result == 'boss_rush':
                    self._start_game('boss_rush')
                elif result == 'survival':
                    self._start_game('survival')
                elif result == 'time_attack':
                    self._start_game('time_attack')
                elif isinstance(result, tuple) and result[0] in ('sector', 'campaign_level'):
                    self._start_game('campaign', result[1])
                elif isinstance(result, tuple) and result[0] == 'buy_skin':
                    self._buy_skin(result[1])
                elif isinstance(result, tuple) and result[0] == 'equip_skin':
                    self._equip_skin(result[1])
                elif isinstance(result, tuple) and result[0] == 'buy_part':
                    self._buy_part(result[1])
                elif isinstance(result, tuple) and result[0] == 'equip_part':
                    self._equip_part(result[1])
                elif result == 'continue':
                    self._load_progress()
                elif result == 'settings':
                    self._previous_state = State.MENU
                    self.state = State.SETTINGS
                elif result == 'codex':
                    data = self._read_save_data()
                    self.codex_screen.set_unlocked(
                        data.get('unlocked_codex', ['scout', 'fighter', 'vanguard']),
                        self.achievements_mgr.unlocked
                    )
                    self._previous_state = State.MENU
                    self.state = State.CODEX
                elif result == 'quit':
                    if self._can_resume_current_run():
                        self._save_progress()
                    self._save_hs()
                    pygame.quit(); sys.exit()
                continue

            # Settings screen
            if self.state == State.SETTINGS:
                res = self.settings_screen.handle_event(event)
                if res == 'changed':
                    self._save_settings()
                elif res == 'back':
                    self._save_settings()
                    self.state = self._previous_state
                continue

            # Codex screen
            if self.state == State.CODEX:
                res = self.codex_screen.handle_event(event)
                if res == 'back':
                    self.state = self._previous_state
                continue

            # Upgrade screen
            if self.state == State.UPGRADE:
                result = self.upg_screen.handle_event(event, self.upgrade_sys, self.player)
                if result == 'chosen':
                    self._after_upgrade()

            if self.state == State.PLAYING and self._pause_button.handle_event(event):
                self.state = State.PAUSED
                continue

            # Paused
            if self.state == State.PAUSED:
                if self._pause_resume_btn.handle_event(event):
                    self.state = State.PLAYING
                if self._pause_settings_btn.handle_event(event):
                    self._previous_state = State.PAUSED
                    self.state = State.SETTINGS
                if self._pause_save_btn.handle_event(event):
                    self._save_progress()
                    self.state = State.MENU
                if self._pause_quit_btn.handle_event(event):
                    self._save_progress()
                    self._save_hs()
                    pygame.quit(); sys.exit()

            # Story — click to skip
            if self.state == State.STORY:
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                    self._begin_sector()

            # Sector clear continue
            if self.state == State.SECTOR_CLEAR:
                if self._continue_btn.handle_event(event):
                    self._next_sector()
                if self._sector_menu_btn.handle_event(event):
                    self._save_progress()
                    self.state = State.MENU

            # Game over
            if self.state == State.GAME_OVER:
                if self._restart_btn.handle_event(event):
                    self._start_game(self.game_mode, self._start_sector)
                if self._menu_btn.handle_event(event):
                    self.state = State.MENU

            # Win screen
            if self.state == State.WIN:
                if self._win_restart_btn.handle_event(event):
                    self._start_game('campaign', 1)
                if self._win_menu_btn.handle_event(event):
                    self.state = State.MENU

    # ── Update ────────────────────────────────────────────────────────────

    def _update(self):
        self.nebula.update()
        self.starfield.update()
        self.flash.update()
        self.camera_shake.update()

        from core.audio import AudioEngine
        audio = AudioEngine()

        if self.state in (State.MENU, State.SETTINGS):
            self.menu.update()
            audio.play_music('menu_music')

        elif self.state == State.STORY:
            self._story_timer += 1
            audio.play_music('menu_music')

        elif self.state == State.PLAYING:
            self._update_playing()
            if self.wave_mgr.boss_active and self._boss_ref and self._boss_ref.alive():
                audio.play_music('boss_music')
            else:
                audio.play_music('gameplay_music')

        elif self.state == State.UPGRADE:
            self.upg_screen.update()
            audio.play_music('gameplay_music')

        elif self.state == State.BOSS_WARN:
            self._boss_warn_timer += 1
            audio.play_music('boss_music')
            if self._boss_warn_timer >= 150:
                self._spawn_boss()

        elif self.state == State.SECTOR_CLEAR:
            self._sector_clear_timer += 1
            audio.play_music('victory_music')

        elif self.state == State.WIN:
            audio.play_music('victory_music')

        elif self.state == State.GAME_OVER:
            audio.stop_music()

    def _update_playing(self):
        # Wave banner
        if self._wave_banner_timer > 0:
            self._wave_banner_timer -= 1

        # Player
        _bullets_before = len(self.bullets)
        self.player.update(self.bullets, self.enemies)
        _new_shots = len(self.bullets) - _bullets_before
        if _new_shots > 0:
            missiles_count = sum(1 for b in self.bullets if isinstance(b, Missile) and b.rect.x <= self.player.rect.right + 60)
            laser_count = _new_shots - max(0, min(missiles_count, _new_shots))
            for _ in range(laser_count):
                self.stats.record_shot(is_missile=False)
            for _ in range(missiles_count):
                self.stats.record_shot(is_missile=True)

        # Missiles target enemies
        for b in self.bullets:
            if isinstance(b, Missile):
                targets = list(self.enemies)
                if self.wave_mgr.boss_active and self._boss_ref and self._boss_ref.alive():
                if self._boss_ref and self._boss_ref.alive():
                    targets.append(self._boss_ref)
                if getattr(self, '_boss_ref2', None) and self._boss_ref2.alive():
                    targets.append(self._boss_ref2)
                b.set_target(targets)

        # Bullets
        self.bullets.update()
        self.e_bullets.update()

        # Explosions & particles
        self.explosions.update()
        self.particles = [p for p in self.particles if p.alive()]
        for p in self.particles:
            p.update()

        # Enemy update + shoot
        for e in list(self.enemies):
            e.update()
            new_bullets = e.try_fire()
            for b in new_bullets:
                self.e_bullets.add(b)

        # ── Collisions ────────────────────────────────────────────────────
        kills_this_frame = 0

        # Player bullets ↔ Enemies
        if self.wave_mgr.boss_active and self._boss_ref:
        # Player bullets ↔ Bosses or Regular Enemies
        if self.wave_mgr.boss_active:
            active_bosses = [boss for boss in (self._boss_ref, getattr(self, '_boss_ref2', None)) if boss and boss.alive()]
            for b in list(self.bullets):
                if not self._boss_ref or not self._boss_ref.alive():
                    break
                if b.rect.colliderect(self._boss_ref.rect):
                    is_missile = isinstance(b, Missile)
                    self.stats.record_hit(b.damage, is_missile=is_missile)
                    if not b.piercing:
                        b.kill()
                    dead = self._boss_ref.hit(b.damage)
                    if dead:
                        self._on_boss_killed()
                for boss in active_bosses:
                    if not boss.alive():
                        continue
                    if b.rect.colliderect(boss.rect):
                        is_missile = isinstance(b, Missile)
                        self.stats.record_hit(b.damage, is_missile=is_missile)
                        dead = boss.hit(b.damage)
                        if not getattr(b, 'piercing', False):
                            b.kill()
                        if dead:
                            self._on_boss_killed(boss)
                        break
        else:
            hit_map = pygame.sprite.groupcollide(
                self.enemies, self.bullets, False, False)
            for enemy, blist in hit_map.items():
                for b in blist:
                    is_missile = isinstance(b, Missile)
                    self.stats.record_hit(b.damage, is_missile=is_missile)
                    dead = enemy.hit(b.damage)
                    if not b.piercing:
                    if not getattr(b, 'piercing', False):
                        b.kill()
                    if dead:
                        self._on_enemy_killed(enemy)
                        kills_this_frame += 1

        # Enemy bullets ↔ Player
        for eb in list(self.e_bullets):
            if eb.rect.colliderect(self.player.rect):
                eb.kill()
                lost_life = self.player.hit(eb.damage)
                self.stats.record_damage_taken(eb.damage)
                self.flash.trigger(RED, 6)
                self.camera_shake.trigger(10, 6)
                if lost_life and self.player.lives <= 0:
                    self._game_over()
                    return

        # Enemies ↔ Player (ram)
        for e in list(self.enemies):
            if e.rect.colliderect(self.player.rect):
                lost_life = self.player.hit(30)
                self.stats.record_damage_taken(30)
                self.flash.trigger(ORANGE, 8)
                self.camera_shake.trigger(16, 10)
                self._on_enemy_killed(e)
                kills_this_frame += 1
                if lost_life and self.player.lives <= 0:
                    self._game_over()
                    return

        # Wave manager tick
        # Wave manager tick (updates both bosses and returns wave/boss signals)
        signal = self.wave_mgr.update(
            self.enemies, self.e_bullets,
            delta_kills=kills_this_frame)

        # Second boss update (Double Boss Surge)
        if hasattr(self, '_boss_ref2') and self._boss_ref2 and self._boss_ref2.alive():
            b2_bullets = self._boss_ref2.update()
            for b in b2_bullets:
                self.e_bullets.add(b)
            # Check player bullets hitting boss2
            hits2 = pygame.sprite.spritecollide(self._boss_ref2, self.bullets, False)
            for b in hits2:
                dmg = getattr(b, 'damage', 10)
                self._boss_ref2.hit(dmg)
                self.stats.record_hit(dmg)
                if not getattr(b, 'piercing', False):
                    b.kill()
                if self._boss_ref2.hp <= 0:
                    cx, cy = self._boss_ref2.rect.center
                    for _ in range(4):
                        self.explosions.add(Explosion(cx + ((_-2)*25), cy, radius=50, color=RED))
                    self.player.score += self._boss_ref2.SCORE // 2
                    self._award_credits(max(50, self._boss_ref2.SCORE // 40))
                    from core.audio import AudioEngine
                    AudioEngine().play('boss_explosion')
                    self.camera_shake.trigger(22, 12)
                    self._boss_ref2.kill()
                    self._boss_ref2 = None
                    break

        if signal == 'upgrade':
            if self.game_mode == 'campaign':
                self._advance_campaign_wave()
            else:
                self._show_upgrade()
        elif signal == 'next_wave':
            self._wave_banner_timer = 90
        elif signal == 'boss_warning':
            self.state = State.BOSS_WARN
            self._boss_warn_timer = 0
            from core.audio import AudioEngine
            AudioEngine().play('boss_warn')
        elif signal == 'sector_clear':
            self._sector_clear()
        elif signal == 'game_clear':
            self._win()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _begin_sector(self):
        self.wave_mgr.start_sector(self.wave_mgr.sector)
        self.state = State.PLAYING
        self._wave_banner_timer = 90

    def _on_enemy_killed(self, enemy):
        cx, cy = enemy.rect.center
        self.explosions.add(Explosion(cx, cy, radius=30, color=ORANGE))
        p = Particle(cx, cy, ORANGE, count=14, speed_range=(1, 5))
        self.particles.append(p)
        pts = enemy.SCORE
        self.player.score += pts
        self._award_credits(max(1, pts // 50))
        from core.audio import AudioEngine
        AudioEngine().play('explosion')
        self.stats.record_enemy_killed()
        enemy_id = getattr(enemy, 'id', 'fighter')
        self._unlock_codex(enemy_id)
        if hasattr(self, 'achievements_mgr'):
            self.achievements_mgr.check_game_events(self)
        if self.game_mode == 'time_attack':
            self.wave_mgr.add_time_bonus(30)
        self.hud.add_kill_floater(cx, cy - 20, pts)
        enemy.kill()

    def _on_boss_killed(self):
        if self._boss_ref:
            cx, cy = self._boss_ref.rect.center
    def _on_boss_killed(self, boss=None):
        target = boss or self._boss_ref
        if target and target.alive():
            is_secondary = (target is getattr(self, '_boss_ref2', None))
            cx, cy = target.rect.center
            for _ in range(6):
                self.explosions.add(Explosion(cx + ((_-3)*30), cy, radius=60, color=RED))
            self.player.score += self._boss_ref.SCORE
            self._award_credits(max(100, self._boss_ref.SCORE // 25))
            score_val = target.SCORE // 2 if is_secondary else target.SCORE
            self.player.score += score_val
            self._award_credits(max(60, score_val // 30))
            from core.audio import AudioEngine
            AudioEngine().play('boss_explosion')
            self.stats.record_boss_killed()
            boss_id = getattr(self._boss_ref, 'NAME', 'Vanguard').lower().split()[0]
            boss_id = getattr(target, 'NAME', 'Vanguard').lower().split()[0]
            self._unlock_codex(boss_id)
            if hasattr(self, 'achievements_mgr'):
                self.achievements_mgr.check_game_events(self)
            if self.game_mode == 'time_attack':
                self.wave_mgr.add_time_bonus(600)
            self._boss_ref.kill()
            self._boss_ref = None
                self.wave_mgr.add_time_bonus(300 if is_secondary else 600)
            target.kill()
            if target is self._boss_ref:
                self._boss_ref = None
                if self.wave_mgr.boss is target:
                    self.wave_mgr.boss = None
            if target is getattr(self, '_boss_ref2', None):
                self._boss_ref2 = None
                if getattr(self.wave_mgr, 'boss2', None) is target:
                    self.wave_mgr.boss2 = None
            self.flash.trigger(WHITE, 14)
            self.camera_shake.trigger(28, 16)

    def _unlock_codex(self, entity_id):
        try:
            data = self._read_save_data()
            unlocked = set(data.get('unlocked_codex', ['scout', 'fighter', 'vanguard']))
            if entity_id not in unlocked:
                unlocked.add(entity_id)
                data['unlocked_codex'] = sorted(unlocked)
                self._apply_profile_to_data(data)
                self._write_save_data(data)
        except Exception:
            pass

    def _spawn_boss(self):
        self.wave_mgr.spawn_boss(self.enemies, self.all_sprites)
        self._boss_ref = self.wave_mgr.boss
        # Double Boss Surge: spawn a secondary boss
        self._boss_ref2 = None
        boss2 = self.wave_mgr.spawn_second_boss(self.enemies, self.all_sprites)
        if boss2:
            self._boss_ref2 = boss2
        self.state = State.PLAYING
        # Clear remaining enemies
        for e in list(self.enemies):
            if e is not self._boss_ref and e is not self._boss_ref2:
                e.kill()
        self.e_bullets.empty()

    def _show_upgrade(self):
        upgrades = self.upgrade_sys.get_available(3)
        if not upgrades:
            self._after_upgrade()
            return
        self.upg_screen.set_upgrades(upgrades)
        self.state = State.UPGRADE

    def _after_upgrade(self):
        if self.game_mode == 'boss_rush':
            self.wave_mgr.prepare_next_boss()
            self.state = State.BOSS_WARN
            self._boss_warn_timer = 0
            return
        if self.game_mode in ('survival', 'time_attack'):
            self.wave_mgr.resume_special_mode()
            self.state = State.PLAYING
            return
        self.wave_mgr.start_next_wave()
        self.state = State.PLAYING
        self._wave_banner_timer = 90

    def _advance_campaign_wave(self):
        self.wave_mgr.start_next_wave()
        self.state = State.PLAYING
        self._wave_banner_timer = 90

    def _sector_clear(self):
        self._record_campaign_clear(self.wave_mgr.sector)
        if hasattr(self, 'achievements_mgr'):
            if self.stats.damage_taken == 0:
                self.achievements_mgr.check_and_unlock('shieldless_run', self)
            if self.stats.accuracy >= 75.0:
                self.achievements_mgr.check_and_unlock('sharpshooter', self)
            if self.wave_mgr.sector == 1:
                self.achievements_mgr.check_and_unlock('campaign_sec1', self)
            self.achievements_mgr.check_game_events(self)
        self._sector_clear_timer = 0
        self.state = State.SECTOR_CLEAR

    def _next_sector(self):
        next_sec = self.wave_mgr.sector + 1
        self.wave_mgr.sector = next_sec
        self.wave_mgr.wave   = 0
        self.state = State.STORY
        self._story_timer = 0

    def _game_over(self):
        self._clear_progress()
        if self.player.score > self.high_score:
            self.high_score = self.player.score
            self._save_hs()
        self.state = State.GAME_OVER

    def _win(self):
        self._record_campaign_clear(TOTAL_SECTORS)
        self._clear_progress()
        if self.player.score > self.high_score:
            self.high_score = self.player.score
            self._save_hs()
        self.state = State.WIN

    # ── Draw ──────────────────────────────────────────────────────────────

    def _draw(self, surf):
        self.screen = surf
        self.screen.fill(BG)
        self.nebula.draw(self.screen)
        self.starfield.draw(self.screen)

        if self.state == State.MENU:
            self.menu.set_has_save(self._has_save())
            unlocked, completed = self._campaign_progress()
            self.menu.set_campaign_progress(unlocked, completed)
            self.menu.set_profile(self.owned_skins, self.equipped_skin,
                                  self.owned_parts, self.equipped_parts)
            self.menu.draw(self.screen, self.high_score, self.credits)

        elif self.state == State.STORY:
            self._draw_story()

        elif self.state in (State.PLAYING, State.BOSS_WARN, State.UPGRADE):
            self._draw_game()
            if self.state == State.BOSS_WARN:
                self._draw_boss_warning()
            elif self.state == State.UPGRADE:
                self.upg_screen.draw(self.screen, self.upgrade_sys)

        elif self.state == State.SECTOR_CLEAR:
            self._draw_game()
            self._draw_sector_clear()

        elif self.state == State.GAME_OVER:
            self._draw_game()
            self._draw_game_over()

        elif self.state == State.WIN:
            self._draw_win()

        elif self.state == State.PAUSED:
            self._draw_game()
            self._draw_paused()

        elif self.state == State.SETTINGS:
            self.settings_screen.draw(self.screen)

        elif self.state == State.CODEX:
            self.codex_screen.draw(self.screen)

        self.flash.draw(self.screen)

    def _draw_game(self):
        # Enemies
        self.enemies.draw(self.screen)
        if self.wave_mgr.boss_active and self._boss_ref and self._boss_ref.alive():
            self.screen.blit(self._boss_ref.image, self._boss_ref.rect)
        # Second boss (Double Boss Surge)
        if hasattr(self, '_boss_ref2') and self._boss_ref2 and self._boss_ref2.alive():
            self.screen.blit(self._boss_ref2.image, self._boss_ref2.rect)
        # Bullets
        self.bullets.draw(self.screen)
        self.e_bullets.draw(self.screen)
        # Explosions
        for exp in self.explosions:
            exp.draw(self.screen)
        # Particles
        for p in self.particles:
            p.draw(self.screen)
        # Player
        self.player.draw(self.screen)
        # HUD
        self.hud.update(self.player.score)
        self.hud.draw(self.screen, self.player, self.wave_mgr)
        if self.wave_mgr.boss_active:
            if self._boss_ref and self._boss_ref.alive():
                self.hud.draw_boss_bar(self.screen, self._boss_ref)
            if hasattr(self, '_boss_ref2') and self._boss_ref2 and self._boss_ref2.alive():
                self.hud.draw_boss_bar(self.screen, self._boss_ref2, offset_y=-125)
            self.hud.draw_boss_bars(self.screen, self._boss_ref, getattr(self, '_boss_ref2', None))
        self._pause_button.draw(self.screen)
        # Wave banner
        if self._wave_banner_timer > 0:
            self.hud.draw_wave_banner(
                self.screen,
                self.wave_mgr.display_sector(),
                self.wave_mgr.display_wave(),
                self._wave_banner_timer, 90,
                self.game_mode)

    def _draw_story(self):
        a    = Assets()
        sec  = self.wave_mgr.sector
        data = SECTOR_STORIES.get(sec, {})

        cx = W // 2
        panel = Panel(cx - 520, H // 2 - 270, 1040, 560, color=(24, 30, 32), border_color=RETRO_MOSS, alpha=235)
        panel.draw(self.screen)

        t1 = a.render('large', data.get('title', ''), RETRO_AMBER)
        t2 = a.render('medium', data.get('subtitle', ''), RETRO_CREAM)
        self.screen.blit(t1, (cx - t1.get_width() // 2, H // 2 - 245))
        self.screen.blit(t2, (cx - t2.get_width() // 2, H // 2 - 192))

        pygame.draw.line(self.screen, RETRO_MOSS, (cx - 430, H // 2 - 152), (cx + 430, H // 2 - 152), 1)

        for i, line in enumerate(data.get('lines', [])):
            visible = self._story_timer > i * 45
            col     = WHITE if visible else (38, 44, 46)
            lt      = a.render_fit(['small', 'tiny'], line, col, 900)
            self.screen.blit(lt, (cx - lt.get_width() // 2, H // 2 - 118 + i * 44))

        target = a.render('medium', f"TARGET: {data.get('boss_name','?')}", RETRO_CRIMSON)
        desc = a.render_fit(['small', 'tiny'], data.get('boss_desc', ''), RETRO_CREAM, 900)
        self.screen.blit(target, (cx - target.get_width() // 2, H // 2 + 150))
        self.screen.blit(desc, (cx - desc.get_width() // 2, H // 2 + 195))

        skip = a.render('small', "Click or press any key to launch", RETRO_SAGE)
        self.screen.blit(skip, (cx - skip.get_width() // 2, H // 2 + 242))

    def _draw_boss_warning(self):
        a     = Assets()
        pulse = 0.5 + 0.5 * math.sin(self.tick * 0.15)
        alpha = int(200 + pulse * 55)

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((40, 15, 15, 75))
        self.screen.blit(overlay, (0, 0))

        t1 = a.render_glow('title', "⚠ BOSS DETECTED ⚠", RETRO_CRIMSON, glow_color=RETRO_TERRA, glow_radius=3)
        t1.set_alpha(alpha)
        self.screen.blit(t1, (W // 2 - t1.get_width() // 2, H // 2 - 50))

        sec    = self.wave_mgr.sector
        bname  = SECTOR_STORIES.get(sec, {}).get('boss_name', '?')
        t2     = a.render('large', bname, RETRO_CREAM)
        t2.set_alpha(int(alpha * 0.9))
        self.screen.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 + 50))

    def _draw_sector_clear(self):
        a = Assets()
        cx = W // 2
        panel = Panel(cx - 450, H // 2 - 260, 900, 540, color=(24, 30, 32), border_color=RETRO_MOSS, alpha=235)
        panel.draw(self.screen)

        sec  = self.wave_mgr.sector
        next_sec = sec + 1

        t1 = a.render_glow('huge', f"SECTOR {sec} CLEARED!", RETRO_SAGE, glow_color=RETRO_MOSS, glow_radius=3)
        t2 = a.render('large', f"SCORE: {self.player.score:,}", RETRO_AMBER)
        t2b = a.render('small', f"CREDITS: {self.credits:,} CR", RETRO_CREAM)
        reward_text = (
            f"FIRST-CLEAR REWARD: +{self._last_campaign_reward} CREDITS"
            if self._last_campaign_reward > 0 else
            "SECTOR REPLAYED (REWARD ALREADY CLAIMED)"
        )
        t2c = a.render('tiny', reward_text, WHITE)
        self.screen.blit(t1, (cx - t1.get_width() // 2, H // 2 - 245))
        self.screen.blit(t2, (cx - t2.get_width() // 2, H // 2 - 165))
        self.screen.blit(t2b, (cx - t2b.get_width() // 2, H // 2 - 120))
        self.screen.blit(t2c, (cx - t2c.get_width() // 2, H // 2 - 90))

        if next_sec <= TOTAL_SECTORS:
            pygame.draw.line(self.screen, RETRO_MOSS, (cx - 380, H // 2 - 60), (cx + 380, H // 2 - 60), 1)
            data = SECTOR_STORIES.get(next_sec, {})
            t3 = a.render('tiny', "UPCOMING THREAT BRIEFING", GREY)
            t4 = a.render('medium', data.get('title', ''), RETRO_AMBER)
            power = campaign_power(self.equipped_parts)
            rec = recommended_power(next_sec)
            power_col = RETRO_SAGE if power >= rec else RETRO_TERRA
            t5 = a.render('small', f"COMBAT POWER: {power}  |  RECOMMENDED: {rec}", power_col)
            self.screen.blit(t3, (cx - t3.get_width() // 2, H // 2 - 45))
            self.screen.blit(t4, (cx - t4.get_width() // 2, H // 2 - 20))
            self.screen.blit(t5, (cx - t5.get_width() // 2, H // 2 + 15))

        self._continue_btn.rect    = pygame.Rect(cx - 240, H // 2 + 185, 230, 52)
        self._sector_menu_btn.rect = pygame.Rect(cx + 10,  H // 2 + 185, 230, 52)
        self._continue_btn.color = RETRO_SAGE
        self._sector_menu_btn.color = RETRO_MOSS

        self._continue_btn.draw(self.screen)
        self._sector_menu_btn.draw(self.screen)

    def _draw_game_over(self):
        a = Assets()
        cx = W // 2
        panel = Panel(cx - 440, H // 2 - 280, 880, 580, color=(24, 30, 32), border_color=RETRO_MOSS, alpha=235)
        panel.draw(self.screen)

        t1 = a.render_glow('huge', "GAME OVER", RETRO_CRIMSON, glow_color=RETRO_TERRA, glow_radius=3)
        self.screen.blit(t1, (cx - t1.get_width() // 2, H // 2 - 265))

        sc_lbl = a.render('tiny', "FINAL SCORE", GREY)
        sc_val = a.render('large', f"{self.player.score:,}", RETRO_AMBER)
        hs_val = a.render('small', f"ALL-TIME BEST: {self.high_score:,}", RETRO_CREAM)
        
        self.screen.blit(sc_lbl, (cx - sc_lbl.get_width() // 2, H // 2 - 180))
        self.screen.blit(sc_val, (cx - sc_val.get_width() // 2, H // 2 - 155))
        self.screen.blit(hs_val, (cx - hs_val.get_width() // 2, H // 2 - 110))

        # ── Combat Performance Metrics Grid ────────────────────────────────
        pygame.draw.line(self.screen, RETRO_MOSS, (cx - 380, H // 2 - 75), (cx + 380, H // 2 - 75), 1)
        grid_title = a.render('tiny', "TACTICAL MISSION DEBRIEF", RETRO_AMBER)
        self.screen.blit(grid_title, (cx - 380, H // 2 - 68))

        rows = self.stats.summary()
        col_w  = 760 // 4
        label_col = RETRO_CREAM
        for i, (label, val) in enumerate(rows):
            col_idx = i % 4
            row_idx = i // 4
            x = (cx - 380) + col_idx * col_w
            y = H // 2 - 40 + row_idx * 55
            ls = a.render('tiny', label, label_col)
            vs = a.render('medium', val, WHITE)
            self.screen.blit(ls, (x, y))
            self.screen.blit(vs, (x, y + 20))

        self._restart_btn.rect = pygame.Rect(cx - 240, H // 2 + 195, 230, 52)
        self._menu_btn.rect    = pygame.Rect(cx + 10,  H // 2 + 195, 230, 52)
        self._restart_btn.color = RETRO_CRIMSON
        self._menu_btn.color = RETRO_MOSS
        self._restart_btn.draw(self.screen)
        self._menu_btn.draw(self.screen)

    def _draw_win(self):
        a = Assets()
        self.screen.fill(BG)
        self.starfield.draw(self.screen)

        cx = W // 2
        panel = Panel(cx - 520, 70, 1040, H - 140, color=(24, 30, 32), border_color=RETRO_MOSS, alpha=235)
        panel.draw(self.screen)

        title = "MISSION ACCOMPLISHED"
        t1    = a.render_glow('huge', title, RETRO_AMBER, glow_color=RETRO_TERRA, glow_radius=3)
        self.screen.blit(t1, (cx - t1.get_width() // 2, 100))

        lines = WIN_TEXT if self.game_mode == 'campaign' else ["MISSION OBJECTIVES COMPLETE"]

        for i, line in enumerate(lines[:6]):
            col = RETRO_AMBER if "HUMANITY" in line else (WHITE if line else GREY)
            lt  = a.render_fit(['medium', 'small', 'tiny'], line, col, 880)
            self.screen.blit(lt, (cx - lt.get_width() // 2, 200 + i * 44))

        sc = a.render('large', f"FINAL SCORE: {self.player.score:,}", RETRO_AMBER)
        self.screen.blit(sc, (cx - sc.get_width() // 2, H - 260))

        self._win_restart_btn.rect = pygame.Rect(cx - 240, H - 150, 230, 52)
        self._win_menu_btn.rect    = pygame.Rect(cx + 10,  H - 150, 230, 52)
        self._win_restart_btn.color = RETRO_SAGE
        self._win_menu_btn.color = RETRO_MOSS
        self._win_restart_btn.draw(self.screen)
        self._win_menu_btn.draw(self.screen)

    def _draw_paused(self):
        a = Assets()
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((16, 20, 22, 185))
        self.screen.blit(overlay, (0, 0))

        cx = W // 2
        panel = Panel(cx - 260, H // 2 - 210, 520, 440, color=(24, 30, 32), border_color=RETRO_MOSS, alpha=235)
        panel.draw(self.screen)

        t = a.render_glow('huge', "PAUSED", RETRO_AMBER, glow_color=RETRO_TERRA, glow_radius=3)
        self.screen.blit(t, (cx - t.get_width() // 2, H // 2 - 195))

        mode_label = self.game_mode.replace('_', ' ').upper()
        line1 = a.render_fit(['small', 'tiny'], f"{mode_label}  ·  {self.wave_mgr.display_time() if self.game_mode in ('survival', 'time_attack') else 'WAVE ' + str(self.wave_mgr.wave)}", RETRO_CREAM, 460)
        line2 = a.render_fit(['small', 'tiny'], f"SCORE: {self.player.score:,}", RETRO_AMBER, 460)
        self.screen.blit(line1, (cx - line1.get_width() // 2, H // 2 - 125))
        self.screen.blit(line2, (cx - line2.get_width() // 2, H // 2 - 95))

        self._pause_resume_btn.rect   = pygame.Rect(cx - 180, H // 2 - 50,  360, 48)
        self._pause_settings_btn.rect = pygame.Rect(cx - 180, H // 2 + 10,  360, 48)
        self._pause_save_btn.rect     = pygame.Rect(cx - 180, H // 2 + 70,  360, 48)
        self._pause_quit_btn.rect     = pygame.Rect(cx - 180, H // 2 + 130, 360, 48)

        self._pause_resume_btn.draw(self.screen)
        self._pause_settings_btn.draw(self.screen)
        self._pause_save_btn.draw(self.screen)
        self._pause_quit_btn.draw(self.screen)

    def _load_settings(self):
        try:
            data = self.saver.read()
            self.settings_screen.load_settings(data)
            from core.audio import AudioEngine
            audio = AudioEngine()
            audio.set_sfx_volume(self.settings_screen.sfx_slider.value)
            audio.set_music_volume(self.settings_screen.music_slider.value)
            audio.set_muted(self.settings_screen.mute_toggle.state)
        except Exception:
            pass

    def _save_settings(self):
        try:
            settings_dict = self.settings_screen.get_settings_dict()
            self.saver.update(settings_dict)
            if hasattr(self, 'player') and self.player:
                if self.settings_screen.current_scheme == 'mouse':
                    self.player.mouse_control = True
                elif self.settings_screen.current_scheme == 'keyboard':
                    self.player.mouse_control = False
                kb = self.settings_screen.keybinds
                self.player.up_key = kb.get('up', pygame.K_w)
                self.player.down_key = kb.get('down', pygame.K_s)
        except Exception:
            pass

    # ── Save / Load ───────────────────────────────────────────────────────

    def _can_resume_current_run(self):
        return self.state in {
            State.STORY,
            State.PLAYING,
            State.BOSS_WARN,
            State.UPGRADE,
            State.SECTOR_CLEAR,
            State.PAUSED,
        }

    def _read_save_data(self):
        return self.saver.read()

    def _write_save_data(self, data):
        self.saver.write(data)

    def _clear_progress(self):
        try:
            data = self._read_save_data()
            for key in SAVE_KEYS:
                data.pop(key, None)
            self._apply_profile_to_data(data)
            self._write_save_data(data)
        except Exception:
            pass

    def _save_progress(self):
        """Save full game state so player can continue later"""
        try:
            self.high_score = max(self.high_score, self.player.score)
            data = self._read_save_data()
            self._apply_profile_to_data(data)
            data.update({
                'high_score':   self.high_score,
                'state':        self.state.name,
                'game_mode':    self.game_mode,
                'sector':       self.wave_mgr.sector,
                'wave':         self.wave_mgr.wave,
                'wave_kills':   self.wave_mgr.wave_kills,
                'score':        self.player.score,
                'lives':        self.player.lives,
                'shield':       self.player.shield,
                'max_shield':   self.player.max_shield,
                'shoot_rate':   self.player.shoot_rate,
                'damage':       self.player.damage,
                'double_shot':  self.player.double_shot,
                'triple_shot':  self.player.triple_shot,
                'piercing':     self.player.piercing,
                'has_missile':  self.player.has_missile,
                'shield_regen': self.player.shield_regen,
                'speed':        self.player.speed,
                'player_y':     self.player.rect.y,
                'upg_levels':   self.upgrade_sys.player_levels,
                'story_timer':  self._story_timer,
                'boss_warn_timer': self._boss_warn_timer,
                'wave_banner_timer': self._wave_banner_timer,
                'mode_timer': self.wave_mgr.mode_timer,
                'next_upgrade_timer': self.wave_mgr.next_upgrade_timer,
                'time_left': self.wave_mgr.time_left,
            })
            self._write_save_data(data)
        except Exception:
            pass

    def _load_progress(self):
        """Restore saved game state"""
        try:
            data = self._read_save_data()
            required = {'sector', 'wave', 'score', 'upg_levels'}
            if not required.issubset(data):
                self._start_game()
                return
            self.game_mode          = data.get('game_mode', 'campaign')
            self._init_play_objects(self.game_mode)
            self.high_score         = max(self.high_score, data.get('high_score', 0))
            p                    = self.player
            p.score              = data.get('score', 0)
            p.lives              = data.get('lives', 3)
            p.rect.y             = data.get('player_y', p.rect.y)
            p.pos_y              = float(p.rect.y)
            if self.game_mode != 'campaign':
                p.shield             = data.get('shield', 100)
                p.max_shield         = data.get('max_shield', 100)
                p.shoot_rate         = data.get('shoot_rate', 18)
                p.damage             = data.get('damage', 10)
                p.double_shot        = data.get('double_shot', False)
                p.triple_shot        = data.get('triple_shot', False)
                p.piercing           = data.get('piercing', False)
                p.has_missile        = data.get('has_missile', False)
                p.shield_regen       = data.get('shield_regen', 0.04)
                p.speed              = data.get('speed', 22)
                self.upgrade_sys.player_levels = data.get('upg_levels', self.upgrade_sys.player_levels)
            else:
                p.shield = min(data.get('shield', p.max_shield), p.max_shield)
            sector               = data.get('sector', 1)
            self._start_sector    = sector
            saved_state          = data.get('state', 'PLAYING')
            self.wave_mgr.sector = sector
            self.wave_mgr.speed_mult = 1.0 + (sector - 1) * (0.14 if self.game_mode == 'campaign' else 0.24)
            self._story_timer       = data.get('story_timer', 0)
            self._boss_warn_timer   = data.get('boss_warn_timer', 0)
            self._wave_banner_timer = data.get('wave_banner_timer', 0)
            self.wave_mgr.mode_timer = data.get('mode_timer', 0)
            self.wave_mgr.next_upgrade_timer = data.get('next_upgrade_timer', 0)
            self.wave_mgr.time_left = data.get('time_left', self.wave_mgr.time_left)

            if saved_state == 'STORY':
                self.wave_mgr.wave = data.get('wave', 1)
                self.state = State.STORY
            elif self.game_mode == 'boss_rush':
                self.wave_mgr.sector = sector
                self.wave_mgr.wave = data.get('wave', sector)
                self.state = State.PLAYING if saved_state == 'PAUSED' else State[saved_state]
                if self.state == State.PLAYING:
                    self.state = State.BOSS_WARN
                    self._boss_warn_timer = 0
            elif self.game_mode == 'survival':
                self.wave_mgr.state = 'survival'
                self.wave_mgr.wave = data.get('wave', 1)
                self.state = State.PLAYING if saved_state == 'PAUSED' else State[saved_state]
            elif self.game_mode == 'time_attack':
                self.wave_mgr.state = 'time_attack'
                self.wave_mgr.wave = data.get('wave', 1)
                self.state = State.PLAYING if saved_state == 'PAUSED' else State[saved_state]
            else:
                self.wave_mgr.wave = data.get('wave', 1) - 1  # start_next_wave increments
                self.wave_mgr.start_next_wave()
                self.wave_mgr.wave_kills = min(
                    data.get('wave_kills', 0),
                    self.wave_mgr.wave_goal
                )
                self.state = State.PLAYING if saved_state == 'PAUSED' else State[saved_state]
            self.menu.set_has_save(True)
        except Exception:
            self._start_game()

    def _has_save(self):
        try:
            data = self._read_save_data()
            return 'sector' in data and data.get('game_mode', 'campaign') == 'campaign'
        except Exception:
            return False

    def _campaign_progress(self):
        data = self._read_save_data()
        inferred_unlocked = 1
        if data.get('game_mode', 'campaign') == 'campaign':
            inferred_unlocked = max(1, min(TOTAL_SECTORS, data.get('sector', 1)))
        inferred_completed = max(0, inferred_unlocked - 1)
        unlocked = data.get('campaign_unlocked_sector', inferred_unlocked)
        completed = data.get('campaign_completed_sector', inferred_completed)
        return unlocked, completed

    def _record_campaign_clear(self, sector):
        if self.game_mode != 'campaign':
            return
        self._last_campaign_reward = 0
        try:
            data = self._read_save_data()
            current_completed = data.get('campaign_completed_sector', 0)
            current_unlocked = data.get('campaign_unlocked_sector', 1)
            if sector > current_completed:
                self._last_campaign_reward = self._campaign_clear_reward(sector)
                self.credits += self._last_campaign_reward
                if sector == 1 and 'laser_cannon_mk2' not in self.owned_parts:
                    self.owned_parts.add('laser_cannon_mk2')
                    self.equipped_parts['laser_cannon'] = 'laser_cannon_mk2'
                data['campaign_rewarded_sector'] = max(data.get('campaign_rewarded_sector', 0), sector)
            data['campaign_completed_sector'] = max(current_completed, sector)
            data['campaign_unlocked_sector'] = max(current_unlocked, min(TOTAL_SECTORS, sector + 1))
            self._apply_profile_to_data(data)
            self._write_save_data(data)
        except Exception:
            pass

    def _campaign_clear_reward(self, sector):
        return 180 + int(sector) * 90

    def _award_credits(self, amount):
        mult = 1.0
        if hasattr(self, 'wave_mgr') and self.wave_mgr:
            diff = getattr(self.wave_mgr, 'difficulty', 'standard')
            if diff in ('hardcore', 'bullet_hell'):
                mult = 1.5
            elif diff == 'double_boss':
                mult = 1.25
        awarded = max(1, int(amount * mult)) if amount > 0 else 0
        self.credits = max(0, self.credits + awarded)
        self._save_profile()

    def _load_profile(self):
        try:
            data = self._ensure_profile_defaults(self._read_save_data())
            self.credits = int(data.get('credits', 0))
            self.owned_skins = set(data.get('owned_skins', ['classic']))
            self.owned_parts = set(data.get('owned_parts', DEFAULT_EQUIPPED_PARTS.values()))
            self.equipped_skin = data.get('equipped_skin', 'classic')
            self.equipped_parts = dict(DEFAULT_EQUIPPED_PARTS)
            self.equipped_parts.update(data.get('equipped_parts', {}))
            if hasattr(self, 'achievements_mgr'):
                self.achievements_mgr.load_unlocked(data.get('unlocked_achievements', []))
            self._sync_campaign_rewards(data)
            self._write_save_data(data)
        except Exception:
            self.credits = 0
            self.owned_skins = {'classic'}
            self.owned_parts = set(DEFAULT_EQUIPPED_PARTS.values())
            self.equipped_skin = 'classic'
            self.equipped_parts = dict(DEFAULT_EQUIPPED_PARTS)

    def _ensure_profile_defaults(self, data):
        """Delegate legacy migration + defaults to SaveManager."""
        return self.saver.ensure_profile_defaults(data, DEFAULT_EQUIPPED_PARTS)

    def _sync_campaign_rewards(self, data):
        completed = int(data.get('campaign_completed_sector', 0))
        rewarded = int(data.get('campaign_rewarded_sector', 0))
        if completed <= rewarded:
            return
        for sector in range(rewarded + 1, completed + 1):
            self.credits += self._campaign_clear_reward(sector)
            if sector == 1 and 'laser_cannon_mk2' not in self.owned_parts:
                self.owned_parts.add('laser_cannon_mk2')
                self.equipped_parts['laser_cannon'] = 'laser_cannon_mk2'
        data['campaign_rewarded_sector'] = completed
        self._apply_profile_to_data(data)

    def _apply_profile_to_data(self, data):
        self._ensure_profile_defaults(data)
        data['credits'] = int(self.credits)
        data['owned_skins'] = sorted(self.owned_skins)
        data['owned_parts'] = sorted(self.owned_parts)
        data['equipped_skin'] = self.equipped_skin
        data['equipped_parts'] = dict(self.equipped_parts)

    def _save_profile(self):
        try:
            data = self._read_save_data()
            self._apply_profile_to_data(data)
            self._write_save_data(data)
        except Exception:
            pass

    def _buy_skin(self, skin_id):
        item = SKINS_BY_ID.get(skin_id)
        if not item or skin_id in self.owned_skins or self.credits < item['cost']:
            return
        self.credits -= item['cost']
        self.owned_skins.add(skin_id)
        self.equipped_skin = skin_id
        self._save_profile()
        self.menu.set_profile(self.owned_skins, self.equipped_skin, self.owned_parts, self.equipped_parts)
        from core.audio import AudioEngine
        AudioEngine().play('upgrade')
        self.hud.show_toast(f"Purchased & Equipped {item['name']}")

    def _equip_skin(self, skin_id):
        if skin_id not in self.owned_skins:
            return
        self.equipped_skin = skin_id
        self._save_profile()
        self.menu.set_profile(self.owned_skins, self.equipped_skin, self.owned_parts, self.equipped_parts)
        from core.audio import AudioEngine
        AudioEngine().play('click')
        item = SKINS_BY_ID.get(skin_id, {'name': 'Skin'})
        self.hud.show_toast(f"Equipped {item['name']}")

    def _buy_part(self, part_id):
        if isinstance(part_id, (tuple, list)):
            part_id = part_id[1]
        item = PARTS_BY_ID.get(part_id)
        if not item or part_id in self.owned_parts or self.credits < item['cost']:
            return
        self.credits -= item['cost']
        self.owned_parts.add(part_id)
        self.equipped_parts[item['category_id']] = part_id
        self._save_profile()
        self.menu.set_profile(self.owned_skins, self.equipped_skin, self.owned_parts, self.equipped_parts)
        from core.audio import AudioEngine
        AudioEngine().play('upgrade')
        self.hud.show_toast(f"Installed {item['name']}")

    def _equip_part(self, part_id):
        if isinstance(part_id, (tuple, list)):
            part_id = part_id[1]
        item = PARTS_BY_ID.get(part_id)
        if not item or part_id not in self.owned_parts:
            return
        self.equipped_parts[item['category_id']] = part_id
        self._save_profile()
        self.menu.set_profile(self.owned_skins, self.equipped_skin, self.owned_parts, self.equipped_parts)
        from core.audio import AudioEngine
        AudioEngine().play('click')
        self.hud.show_toast(f"Equipped {item['name']}")

    def _load_hs(self):
        return self.saver.get_high_score()

    def _save_hs(self):
        self.saver.save_high_score(self.high_score)

