"""
ui/settings_screen.py
---------------------
Warm Retro Settings & Options Screen for Space Impact — Remastered.
Features an organized Audio Mixer, Flight Control Schemes, and
a dedicated, non-overlapping Keybindings Remapper.
"""
import pygame
from core.settings import (W, H, PANEL, BORDER, WHITE, GREY, DGREY,
                            CYAN, GREEN, RED, YELLOW, BLUE, GOLD,
                            RETRO_AMBER, RETRO_TERRA, RETRO_SAGE, RETRO_CREAM, RETRO_CRIMSON, RETRO_MOSS)
from core.assets import Assets
from ui.components import Button, Panel, Slider, ToggleSwitch, draw_text_shadow, draw_glow_rect


KEY_NAMES = {
    pygame.K_w: 'W', pygame.K_s: 'S', pygame.K_a: 'A', pygame.K_d: 'D',
    pygame.K_UP: 'UP', pygame.K_DOWN: 'DOWN', pygame.K_LEFT: 'LEFT', pygame.K_RIGHT: 'RIGHT',
    pygame.K_m: 'M', pygame.K_p: 'P', pygame.K_SPACE: 'SPACE', pygame.K_ESCAPE: 'ESC',
    pygame.K_LSHIFT: 'LSHIFT', pygame.K_RSHIFT: 'RSHIFT', pygame.K_RETURN: 'ENTER',
}


def key_to_name(key_code):
    if key_code in KEY_NAMES:
        return KEY_NAMES[key_code]
    name = pygame.key.name(key_code).upper()
    return name if name else f"KEY_{key_code}"


class SettingsScreen:
    def __init__(self):
        cx = W // 2
        self.panel = Panel(cx - 500, 60, 1000, 610, color=(24, 30, 32), border_color=RETRO_MOSS, alpha=235)

        # Audio Sliders & Toggle (Left Column)
        lx = cx - 440
        self.sfx_slider   = Slider(lx, 195, 380, 20, value=0.7, color=RETRO_AMBER, label="SFX Audio Volume")
        self.music_slider = Slider(lx, 265, 380, 20, value=0.5, color=RETRO_SAGE, label="Soundtrack Volume")
        self.mute_toggle  = ToggleSwitch(lx + 200, 325, w=58, h=28, state=False, label="MUTE ALL AUDIO")

        # Control Scheme Buttons (Right Column)
        rx = cx + 40
        self.scheme_hybrid_btn = Button(rx, 190, 400, 44, "HYBRID (SCROLL + KEYS)", font_key='small', color=RETRO_MOSS)
        self.scheme_mouse_btn  = Button(rx, 245, 400, 44, "DIRECT MOUSE STEERING", font_key='small', color=(28, 34, 36))
        self.scheme_key_btn    = Button(rx, 300, 400, 44, "KEYBOARD-ONLY", font_key='small', color=(28, 34, 36))
        self.current_scheme = 'hybrid'

        # Keybinding Buttons (Neat 4-column row at y = 475)
        kw = 190
        kb_y = 475
        self.keybind_buttons = {
            'up':           Button(cx - 420, kb_y, kw, 44, "W", font_key='small', color=RETRO_MOSS),
            'down':         Button(cx - 200, kb_y, kw, 44, "S", font_key='small', color=RETRO_MOSS),
            'mouse_toggle': Button(cx + 20,  kb_y, kw, 44, "M", font_key='small', color=RETRO_MOSS),
            'pause':        Button(cx + 240, kb_y, kw, 44, "ESC", font_key='small', color=RETRO_MOSS),
        }
        self.keybinds = {
            'up': pygame.K_w,
            'down': pygame.K_s,
            'mouse_toggle': pygame.K_m,
            'pause': pygame.K_ESCAPE,
        }

        self.rebinding_action = None

        # Bottom Actions
        self.reset_btn = Button(cx - 250, 560, 230, 50, "RESET DEFAULTS", color=RETRO_CRIMSON, font_key='small')
        self.back_btn  = Button(cx + 20,  560, 230, 50, "APPLY & BACK", color=RETRO_SAGE, font_key='small')

    def load_settings(self, data):
        self.sfx_slider.value = float(data.get('sfx_volume', 0.7))
        self.music_slider.value = float(data.get('music_volume', 0.5))
        self.mute_toggle.state = bool(data.get('audio_muted', False))
        self.current_scheme = data.get('control_scheme', 'hybrid')
        self._update_scheme_buttons()

        raw_kb = data.get('keybinds', {})
        for act, default_k in [('up', pygame.K_w), ('down', pygame.K_s),
                              ('mouse_toggle', pygame.K_m), ('pause', pygame.K_ESCAPE)]:
            val = raw_kb.get(act)
            if isinstance(val, str) and hasattr(pygame, f"K_{val.lower()}"):
                val = getattr(pygame, f"K_{val.lower()}")
            elif not isinstance(val, int):
                val = default_k
            self.keybinds[act] = val
            if act in self.keybind_buttons:
                self.keybind_buttons[act].text = key_to_name(val)

    def get_settings_dict(self):
        kb_export = {act: key_to_name(k) for act, k in self.keybinds.items()}
        return {
            'sfx_volume': round(self.sfx_slider.value, 2),
            'music_volume': round(self.music_slider.value, 2),
            'audio_muted': self.mute_toggle.state,
            'control_scheme': self.current_scheme,
            'keybinds': kb_export,
        }

    def _update_scheme_buttons(self):
        self.scheme_hybrid_btn.active = (self.current_scheme == 'hybrid')
        self.scheme_mouse_btn.active  = (self.current_scheme == 'mouse')
        self.scheme_key_btn.active    = (self.current_scheme == 'keyboard')

    def handle_event(self, event):
        if self.rebinding_action:
            if event.type == pygame.KEYDOWN:
                if event.key != pygame.K_ESCAPE:
                    self.keybinds[self.rebinding_action] = event.key
                    self.keybind_buttons[self.rebinding_action].text = key_to_name(event.key)
                self.rebinding_action = None
                return 'changed'

        changed = False
        if self.sfx_slider.handle_event(event):
            from core.audio import AudioEngine
            AudioEngine().set_sfx_volume(self.sfx_slider.value)
            changed = True

        if self.music_slider.handle_event(event):
            from core.audio import AudioEngine
            AudioEngine().set_music_volume(self.music_slider.value)
            changed = True

        if self.mute_toggle.handle_event(event):
            from core.audio import AudioEngine
            AudioEngine().set_muted(self.mute_toggle.state)
            changed = True

        if self.scheme_hybrid_btn.handle_event(event):
            self.current_scheme = 'hybrid'
            self._update_scheme_buttons()
            changed = True
        elif self.scheme_mouse_btn.handle_event(event):
            self.current_scheme = 'mouse'
            self._update_scheme_buttons()
            changed = True
        elif self.scheme_key_btn.handle_event(event):
            self.current_scheme = 'keyboard'
            self._update_scheme_buttons()
            changed = True

        for act, btn in self.keybind_buttons.items():
            if btn.handle_event(event):
                self.rebinding_action = act
                btn.text = "PRESS..."
                return 'rebinding'

        if self.reset_btn.handle_event(event):
            self.load_settings({
                'sfx_volume': 0.7, 'music_volume': 0.5, 'audio_muted': False,
                'control_scheme': 'hybrid',
                'keybinds': {'up': 'W', 'down': 'S', 'mouse_toggle': 'M', 'pause': 'ESC'}
            })
            from core.audio import AudioEngine
            AudioEngine().set_sfx_volume(0.7)
            AudioEngine().set_music_volume(0.5)
            AudioEngine().set_muted(False)
            return 'changed'

        if self.back_btn.handle_event(event):
            return 'back'

        return 'changed' if changed else None

    def draw(self, surf):
        a = Assets()
        cx = W // 2
        self.panel.draw(surf)

        # Title
        t = a.render('large', "SYSTEM CONFIGURATION & CONTROLS", RETRO_AMBER)
        surf.blit(t, (cx - t.get_width() // 2, 85))

        # Section 1: Audio Engine
        h1 = a.render('medium', "AUDIO MIXER", RETRO_CREAM)
        surf.blit(h1, (cx - 440, 145))
        self.sfx_slider.draw(surf)
        self.music_slider.draw(surf)
        self.mute_toggle.draw(surf)

        # Section 2: Flight Controls
        h2 = a.render('medium', "FLIGHT CONTROL SCHEME", RETRO_CREAM)
        surf.blit(h2, (cx + 40, 145))
        self.scheme_hybrid_btn.draw(surf)
        self.scheme_mouse_btn.draw(surf)
        self.scheme_key_btn.draw(surf)

        # Divider line
        pygame.draw.line(surf, RETRO_MOSS, (cx - 440, 385), (cx + 440, 385), 1)

        # Section 3: Custom Keybindings Header
        h3 = a.render('medium', "KEYBINDINGS REMAPPER", RETRO_CREAM)
        surf.blit(h3, (cx - 440, 405))

        # Labels for the 4 keybinding columns
        lbl_up   = a.render('tiny', "MOVE UP:", RETRO_CREAM)
        lbl_down = a.render('tiny', "MOVE DOWN:", RETRO_CREAM)
        lbl_m    = a.render('tiny', "MOUSE TOGGLE:", RETRO_CREAM)
        lbl_p    = a.render('tiny', "PAUSE:", RETRO_CREAM)

        surf.blit(lbl_up,   (cx - 420, 448))
        surf.blit(lbl_down, (cx - 200, 448))
        surf.blit(lbl_m,    (cx + 20,  448))
        surf.blit(lbl_p,    (cx + 240, 448))

        for btn in self.keybind_buttons.values():
            btn.draw(surf)

        self.reset_btn.draw(surf)
        self.back_btn.draw(surf)
