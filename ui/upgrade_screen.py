"""
ui/upgrade_screen.py
--------------------
Warm Retro Upgrade Card Selector for Space Impact — Remastered.
Styled with the curated retro color palette:
#dfa05d (Amber), #ac5045 (Terra), #658761 (Sage), #dcc9a9 (Cream), #b83a2d (Crimson), #4e6851 (Moss).
"""
import pygame
import math
from core.settings import (W, H, PANEL, BORDER, WHITE, GREY, DGREY,
                            CYAN, GREEN, YELLOW, ORANGE, RED, PURPLE,
                            BLUE, BG, DARK, GOLD,
                            RETRO_AMBER, RETRO_TERRA, RETRO_SAGE, RETRO_CREAM, RETRO_CRIMSON, RETRO_MOSS)
from core.assets import Assets
from systems.upgrade_system import RARITY_COLORS
from ui.components import Panel, Button, draw_glow_rect, draw_text_shadow


CARD_W   = 360
CARD_H   = 460
CARD_GAP = 40


class UpgradeScreen:
    def __init__(self):
        self._upgrades  = []
        self._hovered   = -1
        self._chosen    = None
        self._tick      = 0
        self._anim_in   = 0

    def set_upgrades(self, upgrades):
        self._upgrades  = upgrades
        self._hovered   = -1
        self._chosen    = None
        self._tick      = 0
        self._anim_in   = 25

    def _card_rects(self):
        n      = len(self._upgrades)
        total  = n * CARD_W + (n - 1) * CARD_GAP
        start  = W // 2 - total // 2
        rects  = []
        for i in range(n):
            x = start + i * (CARD_W + CARD_GAP)
            y = H // 2 - CARD_H // 2 + 30
            rects.append(pygame.Rect(x, y, CARD_W, CARD_H))
        return rects

    def handle_event(self, event, upgrade_system, player):
        rects = self._card_rects()
        if event.type == pygame.MOUSEMOTION:
            self._hovered = -1
            for i, r in enumerate(rects):
                if r.collidepoint(event.pos):
                    self._hovered = i
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(rects):
                if r.collidepoint(event.pos):
                    u = self._upgrades[i]
                    upgrade_system.apply(u['id'], player)
                    self._chosen = i
                    from core.audio import AudioEngine
                    AudioEngine().play('upgrade')
                    return 'chosen'
        return None

    def update(self):
        self._tick += 1
        if self._anim_in > 0:
            self._anim_in -= 1

    def draw(self, surf, upgrade_system):
        a      = Assets()
        alpha  = int(255 * (1 - self._anim_in / 25))

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((14, 18, 20, 215))
        surf.blit(overlay, (0, 0))

        t1 = a.render_glow('huge', "CHOOSE SHIP UPGRADE", RETRO_AMBER, glow_color=RETRO_TERRA, glow_radius=3)
        t2 = a.render('small', "SELECT ONE COMPONENT UPGRADE TO REINFORCE YOUR SHIP", RETRO_CREAM)
        
        t1.set_alpha(alpha)
        t2.set_alpha(alpha)
        surf.blit(t1, (W // 2 - t1.get_width() // 2, 70))
        surf.blit(t2, (W // 2 - t2.get_width() // 2, 138))

        rects = self._card_rects()
        for i, (u, rect) in enumerate(zip(self._upgrades, rects)):
            self._draw_card(surf, u, rect, i, upgrade_system, alpha)

    def _draw_card(self, surf, u, rect, idx, upgrade_system, alpha):
        a        = Assets()
        hovered  = self._hovered == idx
        r_color  = RETRO_SAGE if u['rarity'] == 'common' else (RETRO_AMBER if u['rarity'] == 'rare' else RETRO_TERRA)
        u_color  = u['color']
        level    = upgrade_system.level_of(u['id'])
        max_lv   = u['max']

        draw_rect = rect.copy()
        if hovered:
            draw_rect.y -= 10

        if hovered:
            draw_glow_rect(surf, r_color, draw_rect, radius=14, glow_spread=4, alpha=80)

        card_surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        bg_alpha  = 245 if hovered else 225
        pygame.draw.rect(card_surf, (22, 28, 30, bg_alpha), (0, 0, CARD_W, CARD_H), border_radius=14)
        
        b_color = r_color if hovered else RETRO_MOSS
        pygame.draw.rect(card_surf, (*b_color, 255), (0, 0, CARD_W, CARD_H), 3 if hovered else 2, border_radius=14)
        
        card_surf.set_alpha(alpha)
        surf.blit(card_surf, draw_rect.topleft)

        # Rarity Pill
        rar_pill = pygame.Surface((100, 24), pygame.SRCALPHA)
        pygame.draw.rect(rar_pill, (*r_color, 50), (0, 0, 100, 24), border_radius=12)
        pygame.draw.rect(rar_pill, (*r_color, 230), (0, 0, 100, 24), 1, border_radius=12)
        rar_txt = a.render('tiny', u['rarity'].upper(), r_color)
        rar_pill.blit(rar_txt, (50 - rar_txt.get_width() // 2, 12 - rar_txt.get_height() // 2))
        surf.blit(rar_pill, (draw_rect.x + 18, draw_rect.y + 18))

        icon_cx = draw_rect.centerx
        icon_cy = draw_rect.y + 110
        pygame.draw.circle(surf, (28, 34, 36), (icon_cx, icon_cy), 48)
        pygame.draw.circle(surf, r_color if hovered else RETRO_MOSS, (icon_cx, icon_cy), 48, 2)

        icon_surf = a.render('huge', u['icon'], WHITE)
        surf.blit(icon_surf, (icon_cx - icon_surf.get_width() // 2, icon_cy - icon_surf.get_height() // 2))

        name_surf = a.render_fit(['large', 'medium', 'small'], u['name'].upper(), WHITE, CARD_W - 36)
        surf.blit(name_surf, (icon_cx - name_surf.get_width() // 2, draw_rect.y + 180))

        desc_surf = a.render_fit(['small', 'tiny'], u['desc'], (210, 205, 195), CARD_W - 40)
        surf.blit(desc_surf, (icon_cx - desc_surf.get_width() // 2, draw_rect.y + 225))

        det_surf = a.render_fit(['small', 'tiny'], u['detail'], RETRO_AMBER, CARD_W - 40)
        surf.blit(det_surf, (icon_cx - det_surf.get_width() // 2, draw_rect.y + 265))

        if max_lv > 1:
            pip_total = CARD_W - 60
            pip_w     = pip_total // max_lv - 4
            pip_h     = 10
            py        = draw_rect.y + CARD_H - 100
            for j in range(max_lv):
                px  = draw_rect.x + 30 + j * (pip_w + 4)
                col = r_color if j < level else (34, 40, 42)
                pygame.draw.rect(surf, col, (px, py, pip_w, pip_h), border_radius=3)
            
            lv_surf = a.render('tiny', f"LEVEL {level} / {max_lv}", GREY)
            surf.blit(lv_surf, (icon_cx - lv_surf.get_width() // 2, draw_rect.y + CARD_H - 78))
        else:
            status_txt = "✓ EQUIPPED" if level > 0 else "SINGLE UPGRADE"
            lv_surf = a.render('small', status_txt, RETRO_SAGE if level > 0 else GREY)
            surf.blit(lv_surf, (icon_cx - lv_surf.get_width() // 2, draw_rect.y + CARD_H - 85))

        btn_col = r_color if hovered else RETRO_MOSS
        sel_btn = Button(draw_rect.x + 30, draw_rect.y + CARD_H - 52, CARD_W - 60, 38,
                         "SELECT UPGRADE", color=btn_col, font_key='small', radius=6)
        sel_btn.hovered = hovered
        sel_btn.draw(surf)
