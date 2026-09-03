import pygame
import math
from core.settings import (W, H, PANEL, BORDER, WHITE, GREY, DGREY,
                            CYAN, GREEN, YELLOW, ORANGE, RED, PURPLE,
                            BLUE, BG, DARK)
from core.assets import Assets
from systems.upgrade_system import RARITY_COLORS
from ui.components import Panel, Button, draw_glow


CARD_W  = 340
CARD_H  = 420
CARD_GAP= 50


class UpgradeScreen:
    def __init__(self):
        self._upgrades  = []
        self._hovered   = -1
        self._chosen    = None
        self._tick      = 0
        self._anim_in   = 0   # 0-30 fade-in frames

    def set_upgrades(self, upgrades):
        self._upgrades  = upgrades
        self._hovered   = -1
        self._chosen    = None
        self._tick      = 0
        self._anim_in   = 30

    def _card_rects(self):
        n      = len(self._upgrades)
        total  = n * CARD_W + (n - 1) * CARD_GAP
        start  = W // 2 - total // 2
        rects  = []
        for i in range(n):
            x = start + i * (CARD_W + CARD_GAP)
            y = H // 2 - CARD_H // 2
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
        alpha  = int(255 * (1 - self._anim_in / 30))

        # Dimmed background
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 15, 200))
        surf.blit(overlay, (0, 0))

        # Title
        t1 = a.render('huge',   "CHOOSE UPGRADE", WHITE)
        t2 = a.render('medium', "Select one to continue to the next wave", GREY)
        t1.set_alpha(alpha)
        t2.set_alpha(alpha)
        surf.blit(t1, (W // 2 - t1.get_width() // 2, 80))
        surf.blit(t2, (W // 2 - t2.get_width() // 2, 158))

        rects = self._card_rects()
        for i, (u, rect) in enumerate(zip(self._upgrades, rects)):
            self._draw_card(surf, u, rect, i, upgrade_system, alpha)

    def _draw_card(self, surf, u, rect, idx, upgrade_system, alpha):
        a        = Assets()
        hovered  = self._hovered == idx
        chosen   = self._chosen  == idx
        r_color  = RARITY_COLORS[u['rarity']]
        u_color  = u['color']
        level    = upgrade_system.level_of(u['id'])
        max_lv   = u['max']

        # Hover lift
        draw_rect = rect.copy()
        if hovered:
            draw_rect.y -= 12

        # Glow behind card
        if hovered:
            draw_glow(surf, u_color, draw_rect.centerx, draw_rect.centery,
                      200, alpha=40)

        # Card background
        card_surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        bg_alpha  = 230 if hovered else 200
        pygame.draw.rect(card_surf, (*PANEL, bg_alpha), (0, 0, CARD_W, CARD_H),
                         border_radius=16)
        border_col = u_color if hovered else BORDER
        pygame.draw.rect(card_surf, (*border_col, 255), (0, 0, CARD_W, CARD_H),
                         3, border_radius=16)
        card_surf.set_alpha(alpha)
        surf.blit(card_surf, draw_rect.topleft)

        # Icon background circle
        icon_cx = draw_rect.centerx
        icon_cy = draw_rect.y + 90
        pygame.draw.circle(surf, tuple(c // 4 for c in u_color), (icon_cx, icon_cy), 55)
        pygame.draw.circle(surf, u_color, (icon_cx, icon_cy), 55, 3)

        # Icon text (emoji)
        icon_surf = a.render('huge', u['icon'], u_color)
        icon_surf.set_alpha(alpha)
        surf.blit(icon_surf, (icon_cx - icon_surf.get_width() // 2,
                               icon_cy - icon_surf.get_height() // 2))

        # Rarity badge
        rar_surf = a.render('tiny', u['rarity'].upper(), r_color)
        rar_surf.set_alpha(alpha)
        surf.blit(rar_surf, (draw_rect.x + 14, draw_rect.y + 14))

        # Name
        name_surf = a.render_fit(['medium', 'small', 'tiny'], u['name'], WHITE, CARD_W - 40)
        name_surf.set_alpha(alpha)
        surf.blit(name_surf, (icon_cx - name_surf.get_width() // 2, draw_rect.y + 158))

        # Desc
        desc_surf = a.render_fit(['small', 'tiny'], u['desc'], GREY, CARD_W - 44)
        desc_surf.set_alpha(alpha)
        surf.blit(desc_surf, (icon_cx - desc_surf.get_width() // 2, draw_rect.y + 200))

        # Detail
        det_surf = a.render_fit(['tiny'], u['detail'], u_color, CARD_W - 44)
        det_surf.set_alpha(alpha)
        surf.blit(det_surf, (icon_cx - det_surf.get_width() // 2, draw_rect.y + 234))

        # Level pips
        if max_lv > 1:
            pip_total = CARD_W - 60
            pip_w     = pip_total // max_lv - 4
            pip_h     = 12
            py        = draw_rect.y + CARD_H - 60
            for j in range(max_lv):
                px  = draw_rect.x + 30 + j * (pip_w + 4)
                col = u_color if j < level else DGREY
                pygame.draw.rect(surf, col, (px, py, pip_w, pip_h), border_radius=4)
            lv_surf = a.render('tiny', f"LV {level} / {max_lv}", GREY)
            lv_surf.set_alpha(alpha)
            surf.blit(lv_surf, (icon_cx - lv_surf.get_width() // 2, draw_rect.y + CARD_H - 40))
        else:
            if level > 0:
                lv_surf = a.render('small', "✓ EQUIPPED", GREEN)
            else:
                lv_surf = a.render('small', "CLICK TO EQUIP", u_color)
            lv_surf.set_alpha(alpha)
            surf.blit(lv_surf, (icon_cx - lv_surf.get_width() // 2, draw_rect.y + CARD_H - 78))

        # Hover CTA
        if hovered:
            cta = a.render('small', "SELECT", u_color)
            cta.set_alpha(alpha)
            surf.blit(cta, (icon_cx - cta.get_width() // 2, draw_rect.y + CARD_H - 44))
