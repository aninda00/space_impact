import pygame
from collections.abc import Iterable


class Assets:
    _inst = None

    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
            cls._inst._ready = False
        return cls._inst

    def load(self):
        if self._ready:
            return
        
        font_names = "segoeui,trebuchetms,consolas,arial,dejavusans,helvetica"
        def f(size, bold=True):
            return pygame.font.SysFont(font_names, size, bold=bold)

        def mono(size, bold=True):
            return pygame.font.SysFont("consolas,couriernew,monospace", size, bold=bold)

        self.fonts = {
            'title':   f(84, bold=True),
            'huge':    f(52, bold=True),
            'large':   f(34, bold=True),
            'medium':  f(24, bold=True),
            'small':   f(19, bold=True),
            'tiny':    f(16, bold=True),
            'mono_lg': mono(34, bold=True),
            'mono_md': mono(24, bold=True),
            'mono_sm': mono(18, bold=True),
        }
        self._ready = True

    def font(self, key):
        return self.fonts.get(key, self.fonts['small'])

    def render(self, key, text, color, antialias=True):
        font = self.font(key)
        return font.render(str(text), antialias, color)

    def render_glow(self, key, text, color, glow_color=None, glow_radius=3, antialias=True):
        """Render text with a soft luminous glow aura behind it."""
        font = self.font(key)
        base_surf = font.render(str(text), antialias, color)
        gw, gh = base_surf.get_width() + glow_radius * 4, base_surf.get_height() + glow_radius * 4
        glow_surf = pygame.Surface((gw, gh), pygame.SRCALPHA)
        
        gc = glow_color or color
        # Render diffuse glow halo
        for dx in range(-glow_radius, glow_radius + 1, max(1, glow_radius // 2)):
            for dy in range(-glow_radius, glow_radius + 1, max(1, glow_radius // 2)):
                if dx == 0 and dy == 0:
                    continue
                alpha_val = int(70 / (1 + (dx*dx + dy*dy)**0.5))
                g_text = font.render(str(text), antialias, (*gc[:3], alpha_val))
                glow_surf.blit(g_text, (glow_radius * 2 + dx, glow_radius * 2 + dy))
        
        glow_surf.blit(base_surf, (glow_radius * 2, glow_radius * 2))
        return glow_surf

    def render_fit(self, keys, text, color, max_width, antialias=True):
        if isinstance(keys, str):
            keys = [keys]
        elif not isinstance(keys, Iterable):
            keys = [str(keys)]

        keys = list(keys)
        rendered = self.render(keys[-1], text, color, antialias)
        for key in keys:
            candidate = self.render(key, text, color, antialias)
            if candidate.get_width() <= max_width:
                return candidate
        return rendered

    def render_wrap(self, key, text, color, max_width, line_spacing=4, antialias=True):
        """Word-wrap *text* to fit within *max_width* pixels and return a surface
        tall enough for all lines.  Never overflows horizontally."""
        font = self.font(key)
        words = str(text).split(' ')
        lines = []
        current = ''
        for word in words:
            candidate = (current + ' ' + word).strip()
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word  # single long word: accept as-is
        if current:
            lines.append(current)

        if not lines:
            return pygame.Surface((1, 1), pygame.SRCALPHA)

        line_h = font.get_height()
        total_h = len(lines) * line_h + max(0, len(lines) - 1) * line_spacing
        surf = pygame.Surface((max_width, total_h), pygame.SRCALPHA)
        for i, line in enumerate(lines):
            surf.blit(font.render(line, antialias, color), (0, i * (line_h + line_spacing)))
        return surf
