import pygame
from core.settings import (W, H, PANEL, BORDER, WHITE, GREY, DGREY,
                            BLUE, BLUE_D, CYAN, GREEN, RED, DARK, BG)
from core.assets import Assets


def draw_rounded_rect(surf, color, rect, radius=10, border=0, border_color=None):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surf, border_color, rect, border, border_radius=radius)


def draw_text_shadow(surf, text_surf, pos, shadow=(6, 8, 16), offset=(2, 2)):
    shadow_surf = text_surf.copy()
    shadow_surf.fill((*shadow, 255), special_flags=pygame.BLEND_RGBA_MULT)
    surf.blit(shadow_surf, (pos[0] + offset[0], pos[1] + offset[1]))
    surf.blit(text_surf, pos)


class Button:
    def __init__(self, x, y, w, h, text,
                 color=BLUE, hover_color=None, text_color=WHITE,
                 font_key='medium', radius=10):
        self.rect        = pygame.Rect(x, y, w, h)
        self.text        = text
        self.color       = color
        self.hover_color = hover_color or tuple(min(255, c + 40) for c in color)
        self.text_color  = text_color
        self.font_key    = font_key
        self.radius      = radius
        self.hovered     = False
        self.pressed     = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
                self.hovered = True
                return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed:
                self.pressed = False
            self.hovered = self.rect.collidepoint(event.pos)
        return False

    def draw(self, surf):
        a   = Assets()
        col = self.hover_color if self.hovered else self.color
        # Shadow
        shadow = self.rect.move(0, 4)
        pygame.draw.rect(surf, (0, 0, 0, 100), shadow, border_radius=self.radius)
        # Body
        pygame.draw.rect(surf, col, self.rect, border_radius=self.radius)
        pygame.draw.rect(surf, (235, 240, 255), self.rect, 2, border_radius=self.radius)
        # Text
        font_keys = [self.font_key]
        if self.font_key == 'large':
            font_keys += ['medium', 'small']
        elif self.font_key == 'medium':
            font_keys += ['small', 'tiny']
        elif self.font_key == 'small':
            font_keys += ['tiny']
        t = a.render_fit(font_keys, self.text, self.text_color, self.rect.w - 28)
        pos = (self.rect.centerx - t.get_width() // 2,
               self.rect.centery - t.get_height() // 2)
        draw_text_shadow(surf, t, pos)


class ProgressBar:
    def __init__(self, x, y, w, h, color=CYAN, bg_color=None, radius=6):
        self.rect     = pygame.Rect(x, y, w, h)
        self.color    = color
        self.bg_color = bg_color or DGREY
        self.radius   = radius
        self.value    = 1.0   # 0.0 – 1.0

    def draw(self, surf, value=None):
        v = value if value is not None else self.value
        v = max(0.0, min(1.0, v))
        # Background
        pygame.draw.rect(surf, self.bg_color, self.rect, border_radius=self.radius)
        # Fill
        if v > 0:
            fill = pygame.Rect(self.rect.x, self.rect.y,
                               int(self.rect.w * v), self.rect.h)
            pygame.draw.rect(surf, self.color, fill, border_radius=self.radius)
        # Border
        pygame.draw.rect(surf, BORDER, self.rect, 1, border_radius=self.radius)


class Panel:
    def __init__(self, x, y, w, h, color=None, border_color=None, radius=12, alpha=235):
        self.rect         = pygame.Rect(x, y, w, h)
        self.color        = color or PANEL
        self.border_color = border_color or BORDER
        self.radius       = radius
        self.alpha        = alpha
        self._surf        = pygame.Surface((w, h), pygame.SRCALPHA)

    def draw(self, surf):
        self._surf.fill((0, 0, 0, 0))
        c = (*self.color, self.alpha)
        pygame.draw.rect(self._surf, c, (0, 0, self.rect.w, self.rect.h),
                         border_radius=self.radius)
        pygame.draw.rect(self._surf, (*self.border_color, 255),
                         (0, 0, self.rect.w, self.rect.h), 2,
                         border_radius=self.radius)
        surf.blit(self._surf, self.rect.topleft)


class TextLabel:
    def __init__(self, x, y, text, font_key='small', color=WHITE, center=True):
        self.x       = x
        self.y       = y
        self.text    = text
        self.font_key= font_key
        self.color   = color
        self.center  = center

    def draw(self, surf):
        a   = Assets()
        t   = a.render(self.font_key, self.text, self.color)
        x   = self.x - t.get_width() // 2 if self.center else self.x
        surf.blit(t, (x, self.y))


def draw_glow(surf, color, cx, cy, radius, alpha=80):
    s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(s, (*color, alpha), (radius, radius), radius)
    surf.blit(s, (cx - radius, cy - radius), special_flags=pygame.BLEND_RGBA_ADD)
