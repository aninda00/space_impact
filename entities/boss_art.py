"""
entities/boss_art.py
--------------------
Procedural drawing helpers for boss sprite generation.
Extracted from entities/boss.py for clean separation of art/rendering routines.
"""
import pygame
from core.settings import WHITE, RED, YELLOW


def shade(color, amount):
    """Adjust color brightness by amount (-255 to +255)."""
    return tuple(max(0, min(255, ch + amount)) for ch in color)


def draw_spines(surf, color, w, h, anchors, upper=True):
    """Draw procedural armor spines along the top or bottom of a boss hull."""
    for x, span, height in anchors:
        base_y = h // 2 - span if upper else h // 2 + span
        tip_y = base_y - height if upper else base_y + height
        pygame.draw.polygon(surf, color, [
            (x - span, base_y),
            (x + span, base_y),
            (x, tip_y),
        ])


def draw_eye(surf, cx, cy, rx, ry, glow, pupil=(8, 10, 20)):
    """Draw a glowing alien core/eye with highlight and pupil."""
    pygame.draw.ellipse(surf, shade(glow, -90), (cx - rx - 5, cy - ry - 5, rx * 2 + 10, ry * 2 + 10))
    pygame.draw.ellipse(surf, glow, (cx - rx, cy - ry, rx * 2, ry * 2))
    pygame.draw.ellipse(surf, WHITE, (cx - rx // 3, cy - ry // 2, rx, ry))
    pygame.draw.ellipse(surf, pupil, (cx - rx // 4, cy - ry // 3, max(4, rx // 2), max(6, ry)))


def draw_engine(surf, w, h, color):
    """Draw rear thruster engines with glowing flame exhaust."""
    pygame.draw.rect(surf, shade(color, -80), (w - 36, h // 2 - 18, 34, 36), border_radius=9)
    pygame.draw.rect(surf, color, (w - 24, h // 2 - 10, 22, 20), border_radius=7)
    pygame.draw.polygon(surf, (*shade(color, 40), 170), [
        (w - 2, h // 2 - 12), (w - 2, h // 2 + 12), (w + 18, h // 2)
    ])
