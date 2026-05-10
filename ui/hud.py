import pygame
from core.settings import (W, H, TOTAL_SECTORS, CYAN, GREEN, RED, YELLOW,
                            WHITE, GREY, DGREY, PANEL, BORDER, BLUE, ORANGE)
from core.assets import Assets
from ui.components import ProgressBar, Panel, draw_text_shadow


class HUD:
    def __init__(self):
        self._shield_bar  = ProgressBar(20, 26, 340, 24, color=CYAN)
        self._wave_bar    = ProgressBar(W - 360, 72, 340, 14, color=(80, 200, 100))
        self._panel_top_l = Panel(10, 10, 390, 112, alpha=230)
        self._panel_top_r = Panel(W - 370, 10, 360, 96, alpha=215)
        self._panel_score = Panel(W // 2 - 150, 10, 300, 96, alpha=215)
        self._combo_timer = 0
        self._combo_count = 0
        self._last_score  = 0
        self._floaters    = []   # [(text, x, y, life, max_life)]

    def add_kill_floater(self, x, y, points):
        self._floaters.append([f"+{points}", x, y, 45, 45])

    def update(self, score):
        if score != self._last_score:
            self._last_score = score
        self._floaters = [f for f in self._floaters if f[3] > 0]
        for f in self._floaters:
            f[3] -= 1
            f[2] -= 1   # float upward

    def _blit_text(self, surf, text_surf, pos, shadow=(8, 10, 18), offset=(1, 1)):
        shadow_surf = text_surf.copy()
        shadow_surf.fill((*shadow, 255), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(shadow_surf, (pos[0] + offset[0], pos[1] + offset[1]))
        surf.blit(text_surf, pos)

    def draw(self, surf, player, wave_mgr):
        a = Assets()
        label_color = (235, 240, 255)
        soft_label  = (205, 215, 240)
        self._panel_top_l.draw(surf)
        self._panel_top_r.draw(surf)
        self._panel_score.draw(surf)

        # ── Shield bar (left) ─────────────────────────────────────────────
        shield_ratio = player.shield / player.max_shield
        bar_color    = (
            CYAN   if shield_ratio > 0.60 else
            YELLOW if shield_ratio > 0.30 else
            RED
        )
        self._shield_bar.color = bar_color
        self._shield_bar.draw(surf, shield_ratio)

        # Shield label
        s1 = a.render('small', f"SHIELD  {int(player.shield)}/{int(player.max_shield)}", label_color)
        self._blit_text(surf, s1, (22, 67))

        # ── Score (center) ────────────────────────────────────────────────
        sc = a.render('large', f"{player.score:08d}", WHITE)
        self._blit_text(surf, sc, (W // 2 - sc.get_width() // 2, 16), shadow=(10, 12, 22))
        lbl = a.render('small', "SCORE", label_color)
        self._blit_text(surf, lbl, (W // 2 - lbl.get_width() // 2, 63))

        # ── Wave info (right) ─────────────────────────────────────────────
        self._wave_bar.rect.topleft = (W - 360, 72)
        mode = getattr(wave_mgr, 'mode', 'campaign')
        if mode == 'endless':
            sec_txt = a.render('small', f"ENDLESS TIER {wave_mgr.display_sector()}", label_color)
        elif mode == 'boss_rush':
            sec_txt = a.render('small', f"BOSS {wave_mgr.display_sector()} / {TOTAL_SECTORS}", label_color)
        elif mode == 'survival':
            sec_txt = a.render('small', f"SURVIVAL TIER {wave_mgr.display_sector()}", label_color)
        elif mode == 'time_attack':
            sec_txt = a.render('small', f"TIME ATTACK TIER {wave_mgr.display_sector()}", label_color)
        else:
            sec_txt = a.render('small', f"SECTOR {wave_mgr.display_sector()} / {TOTAL_SECTORS}", label_color)
        if mode == 'survival':
            wav_txt = a.render('small', f"TIME {wave_mgr.display_time()}", WHITE)
        elif mode == 'time_attack':
            wav_txt = a.render('small', f"LEFT {wave_mgr.display_time()}", WHITE)
        elif mode == 'boss_rush':
            wav_txt = a.render('small', "BOSS RUSH", WHITE)
        else:
            wav_txt = a.render('small', f"WAVE {wave_mgr.display_wave()}", WHITE)
        self._blit_text(surf, sec_txt, (W - 345, 18))
        self._blit_text(surf, wav_txt, (W - 345, 43))
        self._wave_bar.draw(surf, wave_mgr.wave_progress())

        # ── Lives (bottom-left drawn by player) ───────────────────────────
        lives_lbl = a.render('small', "LIVES", WHITE)
        self._blit_text(surf, lives_lbl, (20, H - 102))

        # ── Kill floaters ─────────────────────────────────────────────────
        for f in self._floaters:
            text, x, y, life, max_life = f
            alpha = int(255 * life / max_life)
            t     = a.render('small', text, YELLOW)
            t.set_alpha(alpha)
            self._blit_text(surf, t, (x, y), shadow=(20, 12, 0))

    def draw_boss_bar(self, surf, boss):
        boss.draw_healthbar(surf)

    def draw_wave_banner(self, surf, sector, wave, timer, max_timer, mode='campaign'):
        """Flash a wave announcement banner"""
        a     = Assets()
        alpha = min(255, int(510 * min(timer, max_timer - timer) / max_timer))
        panel = pygame.Surface((600, 120), pygame.SRCALPHA)
        panel.fill((10, 15, 35, 200))
        pygame.draw.rect(panel, (*CYAN, alpha), (0, 0, 600, 120), 2, border_radius=12)
        surf.blit(panel, (W // 2 - 300, H // 2 - 60))
        title = "BOSS RUSH" if mode == 'boss_rush' else f"WAVE  {wave}"
        t1 = a.render('huge', title, WHITE)
        if mode in ('endless', 'survival', 'time_attack'):
            label = "TIER"
        elif mode == 'boss_rush':
            label = "BOSS"
        else:
            label = "SECTOR"
        t2 = a.render('medium', f"{label}  {sector}", GREY)
        t1.set_alpha(alpha)
        t2.set_alpha(alpha)
        surf.blit(t1, (W // 2 - t1.get_width() // 2, H // 2 - 50))
        surf.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 + 20))
