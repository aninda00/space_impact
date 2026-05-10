import pygame
import sys
import math
import json
import os
from enum import Enum, auto

from core.settings import (W, H, FPS, TOTAL_SECTORS, BG, DARK, CYAN, WHITE,
                            GREY, RED, YELLOW, GREEN, ORANGE, PURPLE, BLUE, GOLD)
from core.assets import Assets

from entities.player   import Player
from entities.effects  import StarField, Explosion, Particle, ScreenFlash
from entities.bullet   import Missile

from systems.wave_manager   import WaveManager
from systems.upgrade_system import UpgradeSystem
from systems.story          import SECTOR_STORIES, WIN_TEXT
from systems.loadout        import SKINS_BY_ID, PARTS_BY_ID, DEFAULT_EQUIPPED_PARTS

from ui.hud            import HUD
from ui.menu           import MainMenu
from ui.upgrade_screen import UpgradeScreen
from ui.components     import Button, Panel

SAVE_FILE = os.path.join(os.path.dirname(__file__), "save.json")
SAVE_KEYS = (
    'state', 'game_mode', 'sector', 'wave', 'wave_kills', 'score', 'lives', 'shield',
    'max_shield', 'shoot_rate', 'damage', 'double_shot', 'triple_shot',
    'piercing', 'has_missile', 'shield_regen', 'speed', 'player_y',
    'upg_levels', 'story_timer', 'boss_warn_timer', 'wave_banner_timer',
    'mode_timer', 'next_upgrade_timer', 'time_left'
)


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


class Game:
    def __init__(self, screen):
        self.screen  = screen
        self.clock   = pygame.time.Clock()
        a            = Assets()
        a.load()

        self.high_score = self._load_hs()
        self.starfield  = StarField()
        self.menu       = MainMenu()
        self.menu.set_starfield(self.starfield)
        self.flash      = ScreenFlash()
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
        self._pause_resume_btn = Button(W // 2 - 180, H // 2 - 20,  360, 65,
                                        "RESUME",      color=(30, 120, 255))
        self._pause_button = Button(W - 126, 18, 108, 42, "PAUSE",
                                    color=(38, 58, 110), font_key='small')
        self._pause_save_btn   = Button(W // 2 - 180, H // 2 + 65,  360, 60,
                                        "SAVE & QUIT TO MENU", color=(50, 80, 50))
        self._pause_quit_btn   = Button(W // 2 - 180, H // 2 + 145, 360, 55,
                                        "QUIT GAME",   color=(80, 25, 25))

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

    def _start_game(self, mode='campaign', sector=1):
        self._clear_progress()
        self.game_mode = mode
        self._start_sector = max(1, min(TOTAL_SECTORS, int(sector or 1)))
        self._init_play_objects(mode)
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
                if event.key == pygame.K_ESCAPE:
                    if self.state == State.PLAYING:
                        self.state = State.PAUSED
                        continue
                    elif self.state == State.PAUSED:
                        self.state = State.PLAYING
                        continue
                    elif self.state == State.MENU:
                        pygame.quit(); sys.exit()
                if event.key == pygame.K_F5 and self.state == State.PLAYING:
                    self._save_progress()

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
                elif isinstance(result, tuple) and result[0] == 'sector':
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
                elif result == 'quit':
                    if self._can_resume_current_run():
                        self._save_progress()
                    self._save_hs()
                    pygame.quit(); sys.exit()
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
        self.starfield.update()
        self.flash.update()

        if self.state == State.MENU:
            self.menu.update()

        elif self.state == State.STORY:
            self._story_timer += 1

        elif self.state == State.PLAYING:
            self._update_playing()

        elif self.state == State.UPGRADE:
            self.upg_screen.update()

        elif self.state == State.BOSS_WARN:
            self._boss_warn_timer += 1
            if self._boss_warn_timer >= 150:
                self._spawn_boss()

        elif self.state == State.SECTOR_CLEAR:
            self._sector_clear_timer += 1

    def _update_playing(self):
        # Wave banner
        if self._wave_banner_timer > 0:
            self._wave_banner_timer -= 1

        # Player
        self.player.update(self.bullets, self.enemies)

        # Missiles target enemies
        for b in self.bullets:
            if isinstance(b, Missile):
                targets = list(self.enemies)
                if self.wave_mgr.boss_active and self._boss_ref and self._boss_ref.alive():
                    targets.append(self._boss_ref)
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
            for b in list(self.bullets):
                if not self._boss_ref or not self._boss_ref.alive():
                    break
                if b.rect.colliderect(self._boss_ref.rect):
                    if not b.piercing:
                        b.kill()
                    dead = self._boss_ref.hit(b.damage)
                    if dead:
                        self._on_boss_killed()
                        break
        else:
            hit_map = pygame.sprite.groupcollide(
                self.enemies, self.bullets, False, False)
            for enemy, blist in hit_map.items():
                for b in blist:
                    dead = enemy.hit(b.damage)
                    if not b.piercing:
                        b.kill()
                    if dead:
                        self._on_enemy_killed(enemy)
                        kills_this_frame += 1

        # Enemy bullets ↔ Player
        for eb in list(self.e_bullets):
            if eb.rect.colliderect(self.player.rect):
                eb.kill()
                lost_life = self.player.hit(eb.damage)
                self.flash.trigger(RED, 6)
                if lost_life and self.player.lives <= 0:
                    self._game_over()
                    return

        # Enemies ↔ Player (ram)
        for e in list(self.enemies):
            if e.rect.colliderect(self.player.rect):
                lost_life = self.player.hit(30)
                self.flash.trigger(ORANGE, 8)
                self._on_enemy_killed(e)
                kills_this_frame += 1
                if lost_life and self.player.lives <= 0:
                    self._game_over()
                    return

        # Wave manager tick
        signal = self.wave_mgr.update(
            self.enemies, self.e_bullets,
            delta_kills=kills_this_frame)

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
        self.explosions.add(Explosion(cx, cy, size=30, color=ORANGE))
        p = Particle(cx, cy, ORANGE, count=14, speed_range=(1, 5))
        self.particles.append(p)
        pts = enemy.SCORE
        self.player.score += pts
        self._award_credits(max(1, pts // 50))
        if self.game_mode == 'time_attack':
            self.wave_mgr.add_time_bonus(30)
        self.hud.add_kill_floater(cx, cy - 20, pts)
        enemy.kill()

    def _on_boss_killed(self):
        if self._boss_ref:
            cx, cy = self._boss_ref.rect.center
            for _ in range(6):
                self.explosions.add(Explosion(cx + ((_-3)*30), cy, size=60, color=RED))
            self.player.score += self._boss_ref.SCORE
            self._award_credits(max(100, self._boss_ref.SCORE // 25))
            if self.game_mode == 'time_attack':
                self.wave_mgr.add_time_bonus(600)
            self._boss_ref.kill()
            self._boss_ref = None
            self.flash.trigger(WHITE, 14)

    def _spawn_boss(self):
        self.wave_mgr.spawn_boss(self.enemies, self.all_sprites)
        self._boss_ref = self.wave_mgr.boss
        self.state = State.PLAYING
        # Clear remaining enemies
        for e in list(self.enemies):
            if e is not self._boss_ref:
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

        self.flash.draw(self.screen)

    def _draw_game(self):
        # Enemies
        self.enemies.draw(self.screen)
        if self.wave_mgr.boss_active and self._boss_ref and self._boss_ref.alive():
            self.screen.blit(self._boss_ref.image, self._boss_ref.rect)
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
        if self.wave_mgr.boss_active and self._boss_ref:
            self.hud.draw_boss_bar(self.screen, self._boss_ref)
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

        panel = Panel(W // 2 - 520, H // 2 - 270, 1040, 560, alpha=232)
        panel.draw(self.screen)

        t1 = a.render_fit(['large', 'medium', 'small'], data.get('title', ''), CYAN, 960)
        t2 = a.render_fit(['medium', 'small', 'tiny'], data.get('subtitle', ''), YELLOW, 900)
        self.screen.blit(t1, (W // 2 - t1.get_width() // 2, H // 2 - 245))
        self.screen.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 - 192))

        pygame.draw.line(self.screen, GREY,
                         (W // 2 - 430, H // 2 - 152), (W // 2 + 430, H // 2 - 152), 1)

        for i, line in enumerate(data.get('lines', [])):
            # Fade lines in over time
            visible = self._story_timer > i * 45
            col     = WHITE if visible else (35, 40, 55)
            lt      = a.render_fit(['small', 'tiny'], line, col, 900)
            self.screen.blit(lt, (W // 2 - lt.get_width() // 2, H // 2 - 118 + i * 46))

        target = a.render_fit(['medium', 'small'], f"TARGET: {data.get('boss_name','?')}", RED, 900)
        desc = a.render_fit(['small', 'tiny'], data.get('boss_desc', ''), WHITE, 900)
        self.screen.blit(target, (W // 2 - target.get_width() // 2, H // 2 + 152))
        self.screen.blit(desc, (W // 2 - desc.get_width() // 2, H // 2 + 198))

        skip = a.render('small', "Click or press any key to begin", GREY)
        self.screen.blit(skip, (W // 2 - skip.get_width() // 2, H // 2 + 242))

    def _draw_boss_warning(self):
        a     = Assets()
        pulse = 0.5 + 0.5 * math.sin(self.tick * 0.15)
        alpha = int(200 + pulse * 55)
        col   = (int(200 + pulse * 55), int(30 + pulse * 20), 30)

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((60, 0, 0, 60))
        self.screen.blit(overlay, (0, 0))

        t1 = a.render('title', "⚠ BOSS INCOMING ⚠", col)
        t1.set_alpha(alpha)
        self.screen.blit(t1, (W // 2 - t1.get_width() // 2, H // 2 - 50))

        sec    = self.wave_mgr.sector
        bname  = SECTOR_STORIES.get(sec, {}).get('boss_name', '?')
        t2     = a.render('large', bname, WHITE)
        t2.set_alpha(int(alpha * 0.8))
        self.screen.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 + 50))

    def _draw_sector_clear(self):
        a = Assets()
        panel = Panel(W // 2 - 430, H // 2 - 235, 860, 500, alpha=242)
        panel.draw(self.screen)

        sec  = self.wave_mgr.sector
        next_sec = sec + 1

        t1 = a.render_fit(['huge', 'large', 'medium'], f"SECTOR {sec} CLEARED!", GREEN, 780)
        t2 = a.render_fit(['large', 'medium', 'small'], f"SCORE  {self.player.score:,}", YELLOW, 700)
        t2b = a.render_fit(['medium', 'small'], f"CREDITS  {self.credits:,}", GOLD, 700)
        self.screen.blit(t1, (W // 2 - t1.get_width() // 2, H // 2 - 212))
        self.screen.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 - 126))
        self.screen.blit(t2b, (W // 2 - t2b.get_width() // 2, H // 2 - 82))

        if next_sec <= TOTAL_SECTORS:
            data = SECTOR_STORIES.get(next_sec, {})
            t3 = a.render_fit(['large', 'medium', 'small'], "NEXT SECTOR", WHITE, 700)
            t4 = a.render_fit(['medium', 'small', 'tiny'], data.get('title', ''), CYAN, 760)
            self.screen.blit(t3, (W // 2 - t3.get_width() // 2, H // 2 - 20))
            self.screen.blit(t4, (W // 2 - t4.get_width() // 2, H // 2 + 34))

        self._continue_btn.rect.topleft = (W // 2 - 160, H // 2 + 118)
        self._sector_menu_btn.rect.topleft = (W // 2 - 160, H // 2 + 190)

        self._continue_btn.draw(self.screen)
        self._sector_menu_btn.draw(self.screen)

    def _draw_game_over(self):
        a = Assets()
        panel = Panel(W // 2 - 360, H // 2 - 220, 720, 460, alpha=230)
        panel.draw(self.screen)

        t1 = a.render('title',  "GAME OVER", RED)
        t2 = a.render('medium', f"SCORE", GREY)
        t3 = a.render('huge',   f"{self.player.score:,}", WHITE)
        t4 = a.render('medium', f"Best: {self.high_score:,}", YELLOW)
        self.screen.blit(t1, (W // 2 - t1.get_width() // 2, H // 2 - 210))
        self.screen.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 - 110))
        self.screen.blit(t3, (W // 2 - t3.get_width() // 2, H // 2 - 78))
        self.screen.blit(t4, (W // 2 - t4.get_width() // 2, H // 2 - 14))

        self._restart_btn.rect.topleft = (W // 2 - 160, H // 2 + 50)
        self._menu_btn.rect.topleft    = (W // 2 - 160, H // 2 + 130)
        self._restart_btn.draw(self.screen)
        self._menu_btn.draw(self.screen)

    def _draw_win(self):
        a = Assets()
        self.screen.fill(BG)
        self.starfield.draw(self.screen)

        panel = Panel(W // 2 - 520, 80, 1040, H - 160, alpha=228)
        panel.draw(self.screen)

        pulse = 0.5 + 0.5 * math.sin(self.tick * 0.05)
        gold  = (int(200 + pulse * 55), int(160 + pulse * 25), 0)
        mode_titles = {
            'campaign': "VICTORY",
            'boss_rush': "BOSS RUSH CLEAR",
            'survival': "SURVIVAL RUN",
            'time_attack': "TIME ATTACK COMPLETE",
            'endless': "ENDLESS RUN",
        }
        mode_lines = {
            'boss_rush': [
                "Every command ship is scrap.",
                "",
                "Thirteen bosses entered the arena. You left with the score.",
                "",
                "BOSS RUSH COMPLETE",
            ],
            'survival': [
                "The pressure finally broke.",
                "",
                f"You survived for {self.wave_mgr.display_time()} against an escalating fleet.",
                "",
                "SURVIVAL LOG SAVED",
            ],
            'time_attack': [
                "The clock is empty.",
                "",
                "Every second became score. Every kill kept the run alive.",
                "",
                "TIME ATTACK COMPLETE",
            ],
            'endless': [
                "The endless front has gone quiet for now.",
                "",
                f"You reached wave {self.wave_mgr.wave} at enemy tier {self.wave_mgr.display_sector()}.",
                "",
                "ENDLESS RUN COMPLETE",
            ],
        }
        title = mode_titles.get(self.game_mode, "VICTORY")
        lines = WIN_TEXT if self.game_mode == 'campaign' else mode_lines.get(self.game_mode, [])

        t1    = a.render_fit(['huge', 'large'], title, gold, 920)
        self.screen.blit(t1, (W // 2 - t1.get_width() // 2, 120))

        for i, line in enumerate(lines):
            col = GOLD if line in ("HUMANITY ENDURES", "BOSS RUSH COMPLETE", "SURVIVAL LOG SAVED", "TIME ATTACK COMPLETE", "ENDLESS RUN COMPLETE") else (WHITE if line else GREY)
            font_keys = ['medium', 'small', 'tiny'] if col == GOLD else ['small', 'tiny']
            lt  = a.render_fit(font_keys, line, col, 860)
            self.screen.blit(lt, (W // 2 - lt.get_width() // 2, 220 + i * 54))

        sc = a.render_fit(['large', 'medium', 'small'], f"Final Score: {self.player.score:,}", CYAN, 860)
        self.screen.blit(sc, (W // 2 - sc.get_width() // 2, H - 260))
        if self.player.score >= self.high_score:
            hs = a.render_fit(['medium', 'small', 'tiny'], "NEW HIGH SCORE", GOLD, 860)
            self.screen.blit(hs, (W // 2 - hs.get_width() // 2, H - 210))

        self._win_restart_btn.rect.topleft = (W // 2 - 160, H - 165)
        self._win_menu_btn.rect.topleft    = (W // 2 - 160, H - 90)

        self._win_restart_btn.draw(self.screen)
        self._win_menu_btn.draw(self.screen)

    def _draw_paused(self):
        a = Assets()
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        panel = Panel(W // 2 - 260, H // 2 - 170, 520, 430, alpha=235)
        panel.draw(self.screen)

        t = a.render('huge', "PAUSED", WHITE)
        self.screen.blit(t, (W // 2 - t.get_width() // 2, H // 2 - 154))

        mode_label = self.game_mode.replace('_', ' ').upper()
        line1 = a.render_fit(['small', 'tiny'], f"{mode_label}  ·  {self.wave_mgr.display_time() if self.game_mode in ('survival', 'time_attack') else 'WAVE ' + str(self.wave_mgr.wave)}", GREY, 460)
        line2 = a.render_fit(['small', 'tiny'], f"SCORE {self.player.score:,}", GREY, 460)
        self.screen.blit(line1, (W // 2 - line1.get_width() // 2, H // 2 - 64))
        self.screen.blit(line2, (W // 2 - line2.get_width() // 2, H // 2 - 28))

        self._pause_resume_btn.rect.topleft = (W // 2 - 180, H // 2 + 20)
        self._pause_save_btn.rect.topleft   = (W // 2 - 180, H // 2 + 105)
        self._pause_quit_btn.rect.topleft   = (W // 2 - 180, H // 2 + 185)

        self._pause_resume_btn.draw(self.screen)
        self._pause_save_btn.draw(self.screen)
        self._pause_quit_btn.draw(self.screen)

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
        if not os.path.exists(SAVE_FILE):
            return {}
        try:
            with open(SAVE_FILE, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_save_data(self, data):
        with open(SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)

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
            self.wave_mgr.speed_mult = 1.0 + (sector - 1) * 0.24
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
        try:
            data = self._read_save_data()
            current_completed = data.get('campaign_completed_sector', 0)
            current_unlocked = data.get('campaign_unlocked_sector', 1)
            data['campaign_completed_sector'] = max(current_completed, sector)
            data['campaign_unlocked_sector'] = max(current_unlocked, min(TOTAL_SECTORS, sector + 1))
            self._apply_profile_to_data(data)
            self._write_save_data(data)
        except Exception:
            pass

    def _award_credits(self, amount):
        self.credits = max(0, self.credits + int(amount))
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
            self._write_save_data(data)
        except Exception:
            self.credits = 0
            self.owned_skins = {'classic'}
            self.owned_parts = set(DEFAULT_EQUIPPED_PARTS.values())
            self.equipped_skin = 'classic'
            self.equipped_parts = dict(DEFAULT_EQUIPPED_PARTS)

    def _ensure_profile_defaults(self, data):
        if 'owned_parts' not in data:
            legacy_owned = set(data.get('owned_attachments', []))
            owned_parts = set(DEFAULT_EQUIPPED_PARTS.values())
            if 'pulse_cannon' in legacy_owned:
                owned_parts.add('laser_cannon_mk2')
            if 'shield_array' in legacy_owned:
                owned_parts.add('shield_generator_aegis')
            if 'overdrive' in legacy_owned:
                owned_parts.add('plasma_core_overdrive')
            if 'seeker_rack' in legacy_owned:
                owned_parts.add('missile_rack_seeker')
            data['owned_parts'] = sorted(owned_parts)
        if 'equipped_parts' not in data:
            equipped_parts = dict(DEFAULT_EQUIPPED_PARTS)
            legacy_equipped = data.get('equipped_attachment')
            if legacy_equipped == 'pulse_cannon':
                equipped_parts['laser_cannon'] = 'laser_cannon_mk2'
            elif legacy_equipped == 'shield_array':
                equipped_parts['shield_generator'] = 'shield_generator_aegis'
            elif legacy_equipped == 'overdrive':
                equipped_parts['plasma_core'] = 'plasma_core_overdrive'
            elif legacy_equipped == 'seeker_rack':
                equipped_parts['missile_rack'] = 'missile_rack_seeker'
            data['equipped_parts'] = equipped_parts
        data.setdefault('credits', 0)
        data.setdefault('owned_skins', ['classic'])
        data.setdefault('owned_parts', sorted(DEFAULT_EQUIPPED_PARTS.values()))
        data.setdefault('equipped_skin', 'classic')
        data.setdefault('equipped_parts', dict(DEFAULT_EQUIPPED_PARTS))
        data.setdefault('campaign_unlocked_sector', 1)
        data.setdefault('campaign_completed_sector', 0)
        return data

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

    def _equip_skin(self, skin_id):
        if skin_id not in self.owned_skins:
            return
        self.equipped_skin = skin_id
        self._save_profile()

    def _buy_part(self, part_id):
        item = PARTS_BY_ID.get(part_id)
        if not item or part_id in self.owned_parts or self.credits < item['cost']:
            return
        self.credits -= item['cost']
        self.owned_parts.add(part_id)
        self.equipped_parts[item['category_id']] = part_id
        self._save_profile()

    def _equip_part(self, part_id):
        item = PARTS_BY_ID.get(part_id)
        if not item or part_id not in self.owned_parts:
            return
        self.equipped_parts[item['category_id']] = part_id
        self._save_profile()

    def _load_hs(self):
        try:
            return self._read_save_data().get('high_score', 0)
        except Exception:
            return 0

    def _save_hs(self):
        try:
            data = self._read_save_data()
            data['high_score'] = self.high_score
            self._write_save_data(data)
        except Exception:
            pass
