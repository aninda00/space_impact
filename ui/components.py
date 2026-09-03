"""
ui/components.py
----------------
Warm Retro UI Component System for Space Impact — Remastered.
Crafted using the curated retro palette:
#dfa05d (Amber), #ac5045 (Terra), #658761 (Sage), #dcc9a9 (Cream), #b83a2d (Crimson), #4e6851 (Moss).
"""
import pygame
import math
from core.settings import (W, H, PANEL, BORDER, WHITE, GREY, DGREY,
                            BLUE, BLUE_D, CYAN, GREEN, RED, DARK, BG, YELLOW, GOLD, PURPLE,
                            RETRO_AMBER, RETRO_TERRA, RETRO_SAGE, RETRO_CREAM, RETRO_CRIMSON, RETRO_MOSS)
from core.assets import Assets


def draw_glow_rect(surf, color, rect, radius=6, glow_spread=3, alpha=45):
    """Draw a soft warm glowing boundary around a rectangle."""
    g_surf = pygame.Surface((rect.w + glow_spread * 4, rect.h + glow_spread * 4), pygame.SRCALPHA)
    inner_rect = pygame.Rect(glow_spread * 2, glow_spread * 2, rect.w, rect.h)
    for spread in range(glow_spread, 0, -1):
        a = int(alpha * (spread / glow_spread))
        pygame.draw.rect(g_surf, (*color[:3], a), inner_rect.inflate(spread * 2, spread * 2), border_radius=radius + spread)
    surf.blit(g_surf, (rect.x - glow_spread * 2, rect.y - glow_spread * 2), special_flags=pygame.BLEND_RGBA_ADD)


def draw_text_shadow(surf, text_surf, pos, shadow=(14, 18, 16), offset=(2, 2)):
    """Render crisp dropped shadow beneath text."""
    shadow_surf = text_surf.copy()
    shadow_surf.fill((*shadow, 220), special_flags=pygame.BLEND_RGBA_MULT)
    surf.blit(shadow_surf, (pos[0] + offset[0], pos[1] + offset[1]))
    surf.blit(text_surf, pos)


class Panel:
    """Warm Retro Glass Panel with muted earth tones and subtle corner accents."""
    def __init__(self, x, y, w, h, color=None, border_color=None, radius=10, alpha=235, title=""):
        self.rect         = pygame.Rect(x, y, w, h)
        self.color        = color or (26, 33, 35)
        self.border_color = border_color or RETRO_MOSS
        self.radius       = radius
        self.alpha        = alpha
        self.title        = title
        self._surf        = pygame.Surface((w, h), pygame.SRCALPHA)
        self._rebuild_surface()

    def resize(self, w, h):
        self.rect.w = w
        self.rect.h = h
        self._surf = pygame.Surface((w, h), pygame.SRCALPHA)
        self._rebuild_surface()

    def _rebuild_surface(self):
        self._surf.fill((0, 0, 0, 0))
        w, h = self.rect.w, self.rect.h
        
        # Earth tone gradient
        for i in range(h):
            prog = i / max(1, h)
            r = int(self.color[0] * (1.0 - prog * 0.22))
            g = int(self.color[1] * (1.0 - prog * 0.22))
            b = int(self.color[2] * (1.0 - prog * 0.20))
            pygame.draw.line(self._surf, (r, g, b, self.alpha), (self.radius, i), (w - self.radius, i))

        pygame.draw.rect(self._surf, (*self.color, self.alpha), (0, 0, w, h), border_radius=self.radius)
        
        # Soft top sheen
        sheen = pygame.Surface((w - self.radius * 2, 2), pygame.SRCALPHA)
        sheen.fill((255, 255, 255, 30))
        self._surf.blit(sheen, (self.radius, 2))

        # Border
        pygame.draw.rect(self._surf, (*self.border_color, 240), (0, 0, w, h), 2, border_radius=self.radius)

        # Subtle Retro Corner Accents
        c_len = min(14, w // 6)
        pygame.draw.line(self._surf, (*RETRO_CREAM, 180), (2, 8), (c_len, 8), 2)
        pygame.draw.line(self._surf, (*RETRO_CREAM, 180), (w - c_len, 8), (w - 2, 8), 2)

    def draw(self, surf):
        surf.blit(self._surf, self.rect.topleft)
        if self.title:
            a = Assets()
            t = a.render('small', self.title.upper(), RETRO_AMBER)
            surf.blit(t, (self.rect.x + 20, self.rect.y + 12))


class Button:
    """Warm Retro Button with gentle hover lift, bevelled corners, and perfectly contained text."""
    def __init__(self, x, y, w, h, text,
                 color=RETRO_MOSS, hover_color=None, text_color=RETRO_CREAM,
                 font_key='medium', radius=8, subtext=""):
        self.rect        = pygame.Rect(x, y, w, h)
        self.text        = text
        self.subtext     = subtext
        self.color       = color
        self.hover_color = hover_color or tuple(min(255, int(c * 1.25) + 18) for c in color)
        self.text_color  = text_color
        self.font_key    = font_key
        self.radius      = radius
        self.hovered     = False
        self.pressed     = False
        self.active      = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
                self.hovered = True
                from core.audio import AudioEngine
                AudioEngine().play('click')
                return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.pressed = False
            self.hovered = self.rect.collidepoint(event.pos)
        return False

    def draw(self, surf):
        a = Assets()
        draw_rect = self.rect.move(0, -2) if (self.hovered and not self.pressed) else self.rect
        col = self.hover_color if self.hovered else self.color

        # Drop shadow
        s_rect = draw_rect.move(0, 3)
        pygame.draw.rect(surf, (8, 12, 10, 140), s_rect, border_radius=self.radius)

        # Active or Hover Soft Glow
        if self.hovered or self.active:
            glow_c = RETRO_AMBER if not self.active else RETRO_SAGE
            draw_glow_rect(surf, glow_c, draw_rect, radius=self.radius, glow_spread=2, alpha=65)

        # Button Surface
        b_surf = pygame.Surface((draw_rect.w, draw_rect.h), pygame.SRCALPHA)
        for i in range(draw_rect.h):
            factor = 1.12 - (i / max(1, draw_rect.h)) * 0.28
            rc = min(255, int(col[0] * factor))
            gc = min(255, int(col[1] * factor))
            bc = min(255, int(col[2] * factor))
            pygame.draw.line(b_surf, (rc, gc, bc, 245), (self.radius, i), (draw_rect.w - self.radius, i))
        pygame.draw.rect(b_surf, (*col, 245), (0, 0, draw_rect.w, draw_rect.h), border_radius=self.radius)

        # Bezel Border
        border_col = RETRO_CREAM if self.hovered else (min(255, col[0] + 40), min(255, col[1] + 40), min(255, col[2] + 40))
        if self.active:
            border_col = RETRO_AMBER
        pygame.draw.rect(b_surf, (*border_col, 255), (0, 0, draw_rect.w, draw_rect.h), 2 if (self.hovered or self.active) else 1, border_radius=self.radius)
        
        surf.blit(b_surf, draw_rect.topleft)

        t_col = self.text_color if not self.hovered else WHITE
        font_keys = [self.font_key, 'medium', 'small', 'tiny']

        if self.subtext:
            # Use appropriate font sizes to guarantee complete containment
            t = a.render_fit(['medium', 'small', 'tiny'] if self.font_key == 'large' else ['small', 'tiny'], self.text, t_col, draw_rect.w - 14)
            sub = a.render_fit(['tiny'], self.subtext, RETRO_CREAM if self.active else (190, 180, 160), draw_rect.w - 12)
            total_h = t.get_height() + sub.get_height() + 2
            if total_h > draw_rect.h - 6:
                t = a.render_fit(['tiny'], self.text, t_col, draw_rect.w - 14)
                total_h = t.get_height() + sub.get_height() + 1
            start_y = draw_rect.centery - total_h // 2
            
            draw_text_shadow(surf, t, (draw_rect.centerx - t.get_width() // 2, start_y))
            draw_text_shadow(surf, sub, (draw_rect.centerx - sub.get_width() // 2, start_y + t.get_height() + 1))
        else:
            t = a.render_fit(font_keys, self.text, t_col, draw_rect.w - 14)
            pos = (draw_rect.centerx - t.get_width() // 2, draw_rect.centery - t.get_height() // 2)
            draw_text_shadow(surf, t, pos)


class ProgressBar:
    """Warm Retro Segmented Progress & Health Bar."""
    def __init__(self, x, y, w, h, color=RETRO_SAGE, bg_color=None, radius=5, label=""):
        self.rect     = pygame.Rect(x, y, w, h)
        self.color    = color
        self.bg_color = bg_color or (20, 25, 26)
        self.radius   = radius
        self.value    = 1.0
        self.label    = label

    def draw(self, surf, value=None):
        v = value if value is not None else self.value
        v = max(0.0, min(1.0, v))
        
        pygame.draw.rect(surf, self.bg_color, self.rect, border_radius=self.radius)
        
        if v > 0:
            fill_w = max(4, int(self.rect.w * v))
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.h)
            pygame.draw.rect(surf, self.color, fill_rect, border_radius=self.radius)
            
            sheen = pygame.Surface((fill_w, max(2, self.rect.h // 2)), pygame.SRCALPHA)
            sheen.fill((255, 255, 255, 45))
            surf.blit(sheen, (self.rect.x, self.rect.y))

        # Ticks
        ticks = 5
        for i in range(1, ticks):
            tx = self.rect.x + int(self.rect.w * (i / ticks))
            pygame.draw.line(surf, (14, 18, 18), (tx, self.rect.y), (tx, self.rect.bottom - 1), 1)

        pygame.draw.rect(surf, RETRO_MOSS, self.rect, 1, border_radius=self.radius)


class Slider:
    """Warm Retro Audio / Option Slider with glowing track and brass knob."""
    def __init__(self, x, y, w, h, value=0.7, min_val=0.0, max_val=1.0, color=RETRO_AMBER, label=""):
        self.rect     = pygame.Rect(x, y, w, h)
        self.value    = value
        self.min_val  = min_val
        self.max_val  = max_val
        self.color    = color
        self.label    = label
        self.dragging = False

    def handle_event(self, event):
        changed = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.inflate(16, 16).collidepoint(event.pos):
                self.dragging = True
                self._update_val_from_mouse(event.pos[0])
                changed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                changed = True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_val_from_mouse(event.pos[0])
            changed = True
        return changed

    def _update_val_from_mouse(self, mouse_x):
        rel_x = max(0, min(self.rect.w, mouse_x - self.rect.x))
        ratio = rel_x / float(self.rect.w)
        self.value = round(self.min_val + ratio * (self.max_val - self.min_val), 2)

    def draw(self, surf):
        a = Assets()
        if self.label:
            lbl_t = a.render('small', self.label, RETRO_CREAM)
            surf.blit(lbl_t, (self.rect.x, self.rect.y - 24))
            val_t = a.render('small', f"{int(self.value * 100)}%", RETRO_AMBER)
            surf.blit(val_t, (self.rect.right - val_t.get_width(), self.rect.y - 24))

        pygame.draw.rect(surf, (18, 24, 25), self.rect, border_radius=4)
        
        ratio = (self.value - self.min_val) / max(0.001, (self.max_val - self.min_val))
        fill_w = int(self.rect.w * ratio)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.h)
            pygame.draw.rect(surf, self.color, fill_rect, border_radius=4)

        pygame.draw.rect(surf, RETRO_MOSS, self.rect, 1, border_radius=4)

        thumb_x = self.rect.x + fill_w
        thumb_y = self.rect.centery
        pygame.draw.circle(surf, (16, 20, 22), (thumb_x, thumb_y), 11)
        pygame.draw.circle(surf, RETRO_CREAM if self.dragging else self.color, (thumb_x, thumb_y), 9)
        pygame.draw.circle(surf, RETRO_AMBER, (thumb_x, thumb_y), 4)


class ToggleSwitch:
    """Warm Retro Pill Toggle Switch (ON / OFF)."""
    def __init__(self, x, y, w=60, h=28, state=False, label=""):
        self.rect  = pygame.Rect(x, y, w, h)
        self.state = state
        self.label = label

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.state = not self.state
                from core.audio import AudioEngine
                AudioEngine().play('click')
                return True
        return False

    def draw(self, surf):
        a = Assets()
        if self.label:
            lbl = a.render('small', self.label, RETRO_CREAM)
            surf.blit(lbl, (self.rect.x - lbl.get_width() - 16, self.rect.centery - lbl.get_height() // 2))

        bg_col = RETRO_SAGE if self.state else (42, 48, 50)
        pygame.draw.rect(surf, bg_col, self.rect, border_radius=self.rect.h // 2)
        pygame.draw.rect(surf, RETRO_CREAM if self.state else RETRO_MOSS, self.rect, 1, border_radius=self.rect.h // 2)

        thumb_r = self.rect.h // 2 - 3
        thumb_x = self.rect.right - thumb_r - 3 if self.state else self.rect.x + thumb_r + 3
        pygame.draw.circle(surf, RETRO_CREAM, (thumb_x, self.rect.centery), thumb_r)
        
        status_t = a.render('tiny', "ON" if self.state else "OFF", RETRO_CREAM if self.state else GREY)
        surf.blit(status_t, (self.rect.right + 10, self.rect.centery - status_t.get_height() // 2))
