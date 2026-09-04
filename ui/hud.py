"""
ui/hud.py
---------
Warm Retro Cockpit HUD for Space Impact — Remastered.
Styled with the curated retro palette:
#dfa05d (Amber), #ac5045 (Terra), #658761 (Sage), #dcc9a9 (Cream), #b83a2d (Crimson), #4e6851 (Moss).
Features distinct Vital, Score, and Tactical consoles with dedicated Pause positioning.
"""
import pygame
import math
from core.settings import (W, H, TOTAL_SECTORS, CYAN, GREEN, RED, YELLOW,
                            WHITE, GREY, DGREY, PANEL, BORDER, BLUE, ORANGE, GOLD, PURPLE,
                            RETRO_AMBER, RETRO_TERRA, RETRO_SAGE, RETRO_CREAM, RETRO_CRIMSON, RETRO_MOSS)
from core.assets import Assets
from ui.components import ProgressBar, Panel, draw_text_shadow, draw_glow_rect


class HUD:
    def __init__(self):
        # Left Console: Vital Shield & Lives
        self._panel_vital = Panel(24, 16, 360, 84, color=(24, 30, 32), border_color=RETRO_MOSS, alpha=235)
        self._shield_bar  = ProgressBar(42, 44, 320, 18, color=RETRO_SAGE, radius=4)

        # Center Console: Score Odometer
        self._panel_score = Panel(W // 2 - 200, 16, 400, 84, color=(24, 30, 32), border_color=RETRO_MOSS, alpha=235)

        # Right Console: Sector Radar & Wave (Leaves space for Pause Button on far right)
        self._panel_radar = Panel(W - 490, 16, 340, 84, color=(24, 30, 32), border_color=RETRO_MOSS, alpha=235)
        self._wave_bar    = ProgressBar(W - 470, 68, 300, 14, color=RETRO_SAGE, radius=4)

        self._floaters    = []   # [(text, x, y, life, max_life, color)]
        self._toast_text  = ''
        self._toast_life  = 0
        self._toast_max   = 90
        self._pulse_tick  = 0

    def add_kill_floater(self, x, y, points):
        self._floaters.append([f"+{points}", x, y, 45, 45, RETRO_AMBER])

    def show_toast(self, message, duration_frames=100):
        self._toast_text = message
        self._toast_life = duration_frames
        self._toast_max  = duration_frames

    def update(self, score=0):
        self._pulse_tick += 1
        self._floaters = [f for f in self._floaters if f[3] > 0]
        for f in self._floaters:
            f[3] -= 1
            f[2] -= 1.2
        if self._toast_life > 0:
            self._toast_life -= 1

    def draw(self, surf, player, wave_mgr):
        a = Assets()
        self._panel_vital.draw(surf)
        self._panel_score.draw(surf)
        self._panel_radar.draw(surf)

        # ── Left Console: Shield & Hull Status ─────────────────────────────
        shield_ratio = player.shield / float(max(1, player.max_shield))
        if shield_ratio < 0.30:
            pulse = math.sin(self._pulse_tick * 0.2) * 0.5 + 0.5
            bar_color = RETRO_CRIMSON if pulse > 0.4 else RETRO_TERRA
        elif shield_ratio < 0.60:
            bar_color = RETRO_AMBER
        else:
            bar_color = RETRO_SAGE

        self._shield_bar.color = bar_color
        self._shield_bar.draw(surf, shield_ratio)

        s_lbl = a.render('tiny', "ENERGY SHIELD", RETRO_CREAM)
        s_val = a.render('small', f"{int(player.shield)} / {int(player.max_shield)}", WHITE)
        surf.blit(s_lbl, (42, 23))
        surf.blit(s_val, (362 - s_val.get_width(), 21))

        # Lives Mini Ships
        for i in range(player.lives):
            lx = 42 + i * 34
            ly = 68
            surf.blit(player.mini_image, (lx, ly))

        # ── Center Console: Score Odometer ─────────────────────────────────
        sc_lbl = a.render('tiny', "COMBAT SCORE", RETRO_CREAM)
        surf.blit(sc_lbl, (W // 2 - sc_lbl.get_width() // 2, 22))
        
        sc_val = a.render('mono_lg', f"{player.score:08d}", RETRO_AMBER)
        surf.blit(sc_val, (W // 2 - sc_val.get_width() // 2, 42))

        # ── Right Console: Tactical Radar & Waves ──────────────────────────
        mode = getattr(wave_mgr, 'mode', 'campaign')
        if mode == 'endless':
            sec_str = f"TIER {wave_mgr.display_sector()}"
            wav_str = f"WAVE {wave_mgr.display_wave()}"
        elif mode == 'boss_rush':
            sec_str = f"BOSS {wave_mgr.display_sector()} / {TOTAL_SECTORS}"
            wav_str = "ARENA"
        elif mode == 'survival':
            sec_str = f"SURVIVAL TIER {wave_mgr.display_sector()}"
            wav_str = f"TIME {wave_mgr.display_time()}"
        elif mode == 'time_attack':
            sec_str = f"TIME ATTACK"
            wav_str = f"REMAINING {wave_mgr.display_time()}"
        else:
            sec_str = f"SECTOR {wave_mgr.display_sector()} / {TOTAL_SECTORS}"
            wav_str = f"WAVE {wave_mgr.display_wave()}"

        r_lbl = a.render('tiny', sec_str, RETRO_CREAM)
        r_val = a.render('small', wav_str, WHITE)
        surf.blit(r_lbl, (W - 470, 23))
        surf.blit(r_val, (W - 170 - r_val.get_width(), 21))

        self._wave_bar.draw(surf, wave_mgr.wave_progress())

        # ── Floating Kill Metrics ──────────────────────────────────────────
        for text, fx, fy, life, max_life, col in self._floaters:
            alpha = int(255 * (life / max_life))
            f_surf = a.render('medium', text, col)
            f_surf.set_alpha(alpha)
            surf.blit(f_surf, (int(fx), int(fy)))

        # ── Toast Notification Pill ────────────────────────────────────────
        if self._toast_life > 0:
            t_alpha = min(255, int(510 * min(self._toast_life, self._toast_max - self._toast_life) / self._toast_max))
            t_text = a.render('small', self._toast_text, RETRO_AMBER)
            
            pw = t_text.get_width() + 44
            ph = 42
            px = W // 2 - pw // 2
            py = H - 80

            pill = pygame.Surface((pw, ph), pygame.SRCALPHA)
            pygame.draw.rect(pill, (24, 30, 32, t_alpha), (0, 0, pw, ph), border_radius=ph // 2)
            pygame.draw.rect(pill, (*RETRO_AMBER, t_alpha), (0, 0, pw, ph), 2, border_radius=ph // 2)
            
            t_text.set_alpha(t_alpha)
            pill.blit(t_text, (22, ph // 2 - t_text.get_height() // 2))
            surf.blit(pill, (px, py))

    def _draw_single_boss_bar(self, surf, boss, bx, by, bw, label_prefix=""):
        if not boss or not boss.alive():
            return
        a = Assets()
        total_h = 44
        panel = pygame.Surface((bw, total_h), pygame.SRCALPHA)
        panel.fill((18, 24, 28, 215))
        pygame.draw.rect(panel, (*RETRO_TERRA, 220), (0, 0, bw, total_h), 2, border_radius=8)

        # Title / Label
        name_str = f"{label_prefix}{boss.NAME}".strip()
        title_t = a.render_fit(['small', 'tiny'], name_str, RETRO_AMBER, bw - 150)
        panel.blit(title_t, (12, 5))

        # HP numbers
        hp_str = f"{int(boss.hp):,} / {int(boss.max_hp):,}"
        hp_num_t = a.render('tiny', hp_str, RETRO_CREAM)
        panel.blit(hp_num_t, (bw - hp_num_t.get_width() - 12, 7))

        # Bars area
        bar_x = 12
        bar_w = bw - 24

        # Shield bar (if max_shield > 0)
        if getattr(boss, 'max_shield', 0) > 0:
            sh_h = 4
            sh_y = 23
            sh_ratio = max(0.0, min(1.0, boss.shield / boss.max_shield))
            pygame.draw.rect(panel, (25, 40, 55), (bar_x, sh_y, bar_w, sh_h), border_radius=2)
            if sh_ratio > 0:
                pygame.draw.rect(panel, CYAN, (bar_x, sh_y, int(bar_w * sh_ratio), sh_h), border_radius=2)
            hp_y = 29
            hp_h = 10
        else:
            hp_y = 24
            hp_h = 13

        # Hull HP bar
        hp_ratio = max(0.0, min(1.0, boss.hp / boss.max_hp))
        pygame.draw.rect(panel, (40, 20, 25), (bar_x, hp_y, bar_w, hp_h), border_radius=3)
        if hp_ratio > 0:
            phase_colors = [RETRO_CRIMSON, RETRO_TERRA, RETRO_AMBER, RETRO_CREAM]
            p_idx = min(len(phase_colors) - 1, max(0, getattr(boss, 'phase', 1) - 1))
            col = phase_colors[p_idx]
            pygame.draw.rect(panel, col, (bar_x, hp_y, int(bar_w * hp_ratio), hp_h), border_radius=3)
            # Subtle highlight sheen on upper half
            pygame.draw.rect(panel, (255, 255, 255, 40), (bar_x, hp_y, int(bar_w * hp_ratio), hp_h // 2), border_radius=2)

        surf.blit(panel, (bx, by))

    def draw_boss_bars(self, surf, boss1, boss2=None):
        b1_alive = boss1 and boss1.alive()
        b2_alive = boss2 and boss2.alive()

        by = H - 56
        if b1_alive and b2_alive:
            # Dual Bosses: Place side-by-side along bottom rim with zero obstruction
            bw = 580
            gap = 30
            bx1 = W // 2 - bw - gap // 2
            bx2 = W // 2 + gap // 2
            self._draw_single_boss_bar(surf, boss1, bx1, by, bw, label_prefix="[ALPHA] ")
            self._draw_single_boss_bar(surf, boss2, bx2, by, bw, label_prefix="[BETA] ")
        elif b1_alive:
            bw = 720
            bx = W // 2 - bw // 2
            self._draw_single_boss_bar(surf, boss1, bx, by, bw)
        elif b2_alive:
            bw = 720
            bx = W // 2 - bw // 2
            self._draw_single_boss_bar(surf, boss2, bx, by, bw, label_prefix="[TITAN] ")

    def draw_boss_bar(self, surf, boss, offset_y=0):
        boss.draw_healthbar(surf, offset_y=offset_y)
        self.draw_boss_bars(surf, boss)

    def draw_wave_banner(self, surf, sector, wave, timer, max_timer, mode='campaign'):
        """Flash warm retro wave announcement banner."""
        a = Assets()
        alpha = min(255, int(510 * min(timer, max_timer - timer) / max_timer))
        
        panel = pygame.Surface((620, 120), pygame.SRCALPHA)
        panel.fill((22, 28, 30, int(alpha * 0.92)))
        pygame.draw.rect(panel, (*RETRO_AMBER, alpha), (0, 0, 620, 120), 2, border_radius=10)
        
        title = "BOSS CLASH" if mode == 'boss_rush' else f"WAVE  {wave}"
        t1 = a.render('huge', title, WHITE)
        t2 = a.render('medium', f"SECTOR  {sector}", RETRO_CREAM)
        
        t1.set_alpha(alpha)
        t2.set_alpha(alpha)
        panel.blit(t1, (310 - t1.get_width() // 2, 20))
        panel.blit(t2, (310 - t2.get_width() // 2, 75))
        
        surf.blit(panel, (W // 2 - 310, H // 2 - 60))
