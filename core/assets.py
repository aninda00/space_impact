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
        def f(name, size, bold=False):
            return pygame.font.SysFont(name, size, bold=bold)

        self.fonts = {
            'title':  f("segoeui", 96,  bold=True),
            'huge':   f("segoeui", 64,  bold=True),
            'large':  f("segoeui", 40,  bold=True),
            'medium': f("segoeui", 28,  bold=True),
            'small':  f("segoeui", 20,  bold=True),
            'tiny':   f("segoeui", 15,  bold=True),
        }
        self._ready = True

    def font(self, key):
        return self.fonts[key]

    def render(self, key, text, color, antialias=True):
        return self.fonts[key].render(text, antialias, color)

    def render_fit(self, keys, text, color, max_width, antialias=True):
        if isinstance(keys, str):
            keys = [keys]
        elif not isinstance(keys, Iterable):
            keys = [str(keys)]

        keys = list(keys)
        rendered = self.render(keys[-1], text, color, antialias)
        for key in keys:
            candidate = self.render(key, text, color, antialias)
            rendered = candidate
            if candidate.get_width() <= max_width:
                break
        return rendered
