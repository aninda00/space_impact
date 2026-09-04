"""
ui/codex_screen.py
------------------
Warm Retro Codex & Achievement Terminal for Space Impact — Remastered.
Styled with the retro palette: #dfa05d, #ac5045, #658761, #dcc9a9, #b83a2d, #4e6851.
"""
import pygame
from core.settings import (W, H, PANEL, BORDER, WHITE, GREY, DGREY,
                            CYAN, GREEN, RED, YELLOW, BLUE, GOLD, ORANGE, PURPLE,
                            RETRO_AMBER, RETRO_TERRA, RETRO_SAGE, RETRO_CREAM, RETRO_CRIMSON, RETRO_MOSS)
from core.assets import Assets
from ui.components import Button, Panel, draw_text_shadow, draw_glow_rect
from systems.codex import ENEMY_CODEX, BOSS_CODEX
from systems.achievements import ACHIEVEMENTS


class CodexScreen:
    def __init__(self):
        cx = W // 2
        self.panel = Panel(cx - 520, 60, 1040, 620, color=(24, 30, 32), border_color=RETRO_MOSS, alpha=235)
        self.current_tab = 'enemies'

        tab_w = 235
        self.tab_enemies_btn = Button(cx - 480, 125, tab_w, 44, "ENEMIES", font_key='small', color=RETRO_MOSS)
        self.tab_bosses_btn  = Button(cx - 235, 125, tab_w, 44, "BOSSES", font_key='small', color=(28, 34, 36))
        self.tab_ship_btn    = Button(cx + 10,  125, tab_w, 44, "SHIP TECH", font_key='small', color=(28, 34, 36))
        self.tab_ach_btn     = Button(cx + 255, 125, tab_w, 44, "ACHIEVEMENTS", font_key='small', color=(28, 34, 36))

        self.back_btn = Button(cx - 130, 620, 260, 48, "BACK TO MENU", color=RETRO_MOSS, font_key='small')

        self.selected_index = 0
        self.unlocked_codex = set()
        self.unlocked_achievements = set()
        self._update_tab_buttons()

    def set_unlocked(self, codex_set, achievements_set):
        self.unlocked_codex = set(codex_set or [])
        self.unlocked_achievements = set(achievements_set or [])

    def _update_tab_buttons(self):
        self.tab_enemies_btn.active = (self.current_tab == 'enemies')
        self.tab_bosses_btn.active  = (self.current_tab == 'bosses')
        self.tab_ship_btn.active    = (self.current_tab == 'shipyard')
        self.tab_ach_btn.active     = (self.current_tab == 'achievements')

    def handle_event(self, event):
        if self.tab_enemies_btn.handle_event(event):
            self.current_tab = 'enemies'
            self.selected_index = 0
            self._update_tab_buttons()
        elif self.tab_bosses_btn.handle_event(event):
            self.current_tab = 'bosses'
            self.selected_index = 0
            self._update_tab_buttons()
        elif self.tab_ship_btn.handle_event(event):
            self.current_tab = 'shipyard'
            self.selected_index = 0
            self._update_tab_buttons()
        elif self.tab_ach_btn.handle_event(event):
            self.current_tab = 'achievements'
            self.selected_index = 0
            self._update_tab_buttons()

        if self.back_btn.handle_event(event):
            return 'back'

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            cx = W // 2
            list_x, list_y, list_w = cx - 480, 195, 290
            if self.current_tab == 'enemies':
                enemy_keys = list(ENEMY_CODEX.keys())
                for i in range(len(enemy_keys)):
                    ey = list_y + 8 + i * 55
                    rect = pygame.Rect(list_x + 8, ey, list_w - 16, 48)
                    if rect.collidepoint(event.pos):
                        self.selected_index = i
                        from core.audio import AudioEngine
                        AudioEngine().play('click')
                        return 'selected'
            elif self.current_tab == 'bosses':
                boss_keys = list(BOSS_CODEX.keys())
                for i in range(len(boss_keys)):
                    ey = list_y + 8 + i * 76
                    rect = pygame.Rect(list_x + 8, ey, list_w - 16, 68)
                    if rect.collidepoint(event.pos):
                        self.selected_index = i
                        from core.audio import AudioEngine
                        AudioEngine().play('click')
                        return 'selected'

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
            elif event.key == pygame.K_DOWN:
                self.selected_index += 1

        return None

    def draw(self, surf):
        a = Assets()
        cx = W // 2
        self.panel.draw(surf)

        # Title
        t = a.render('large', "TACTICAL ENEMY & COMBAT DATABASE", RETRO_AMBER)
        surf.blit(t, (cx - t.get_width() // 2, 78))

        self.tab_enemies_btn.draw(surf)
        self.tab_bosses_btn.draw(surf)
        self.tab_ship_btn.draw(surf)
        self.tab_ach_btn.draw(surf)

        pygame.draw.line(surf, RETRO_MOSS, (cx - 480, 180), (cx + 480, 180), 1)

        if self.current_tab == 'enemies':
            self._draw_enemies_tab(surf, a)
        elif self.current_tab == 'bosses':
            self._draw_bosses_tab(surf, a)
        elif self.current_tab == 'shipyard':
            self._draw_shipyard_tab(surf, a)
        elif self.current_tab == 'achievements':
            self._draw_achievements_tab(surf, a)

        self.back_btn.draw(surf)

    def _draw_enemies_tab(self, surf, a):
        enemy_keys = list(ENEMY_CODEX.keys())
        self.selected_index = max(0, min(len(enemy_keys) - 1, self.selected_index))

        cx = W // 2
        list_x, list_y, list_w, list_h = cx - 480, 195, 290, 410
        pygame.draw.rect(surf, (20, 26, 28), (list_x, list_y, list_w, list_h), border_radius=8)

        for i, key in enumerate(enemy_keys):
            entry = ENEMY_CODEX[key]
            unlocked = key in self.unlocked_codex or True
            ey = list_y + 8 + i * 55
            rect = pygame.Rect(list_x + 8, ey, list_w - 16, 48)

            is_sel = (i == self.selected_index)
            col = RETRO_MOSS if is_sel else (28, 34, 36)
            pygame.draw.rect(surf, col, rect, border_radius=6)
            if is_sel:
                pygame.draw.rect(surf, RETRO_AMBER, rect, 2, border_radius=6)

            title_str = entry['name'] if unlocked else "??? UNKNOWN"
            t = a.render('small', title_str, WHITE if unlocked else GREY)
            surf.blit(t, (rect.x + 12, rect.centery - t.get_height() // 2))

        sel_key = enemy_keys[self.selected_index]
        entry = ENEMY_CODEX[sel_key]
        det_x, det_y, det_w, det_h = cx - 170, 195, 650, 410
        pygame.draw.rect(surf, (20, 26, 28), (det_x, det_y, det_w, det_h), border_radius=8)
        pygame.draw.rect(surf, RETRO_MOSS, (det_x, det_y, det_w, det_h), 2, border_radius=8)

        title_t = a.render('large', entry['name'].upper(), RETRO_AMBER)
        surf.blit(title_t, (det_x + 24, det_y + 18))

        threat_col = RETRO_SAGE if entry['threat'] == 'LOW' else (RETRO_AMBER if entry['threat'] == 'MEDIUM' else RETRO_CRIMSON)
        th_t = a.render('small', f"THREAT: {entry['threat']}", threat_col)
        surf.blit(th_t, (det_x + det_w - th_t.get_width() - 24, det_y + 24))

        pygame.draw.line(surf, RETRO_MOSS, (det_x + 20, det_y + 60), (det_x + det_w - 20, det_y + 60), 1)

        s1 = a.render('small', f"HP: {entry['hp']}    SPEED: {entry['speed']}    VALUE: {entry['score']} PTS", RETRO_CREAM)
        surf.blit(s1, (det_x + 24, det_y + 75))

        d_head = a.render('tiny', "TACTICAL PROFILE:", GREY)
        surf.blit(d_head, (det_x + 24, det_y + 120))
        desc_t = a.render_wrap('small', entry['desc'], WHITE, det_w - 48)
        surf.blit(desc_t, (det_x + 24, det_y + 145))

        t_head = a.render('tiny', "COMBAT COUNTER-MEASURES:", GREY)
        surf.blit(t_head, (det_x + 24, det_y + 220))
        tac_t = a.render_wrap('small', entry['tactics'], RETRO_SAGE, det_w - 48)
        surf.blit(tac_t, (det_x + 24, det_y + 245))

    def _draw_bosses_tab(self, surf, a):
        boss_keys = list(BOSS_CODEX.keys())
        self.selected_index = max(0, min(len(boss_keys) - 1, self.selected_index))

        cx = W // 2
        list_x, list_y, list_w, list_h = cx - 480, 195, 290, 410
        pygame.draw.rect(surf, (20, 26, 28), (list_x, list_y, list_w, list_h), border_radius=8)

        for i, key in enumerate(boss_keys):
            entry = BOSS_CODEX[key]
            ey = list_y + 8 + i * 76
            rect = pygame.Rect(list_x + 8, ey, list_w - 16, 68)

            is_sel = (i == self.selected_index)
            col = RETRO_TERRA if is_sel else (28, 34, 36)
            pygame.draw.rect(surf, col, rect, border_radius=6)
            if is_sel:
                pygame.draw.rect(surf, RETRO_CRIMSON, rect, 2, border_radius=6)

            t = a.render_fit(['small', 'tiny'], entry['name'], WHITE, list_w - 40)
            sec_t = a.render('tiny', entry['sector'], RETRO_CREAM)
            surf.blit(t, (rect.x + 12, rect.y + 12))
            surf.blit(sec_t, (rect.x + 12, rect.y + 38))

        sel_key = boss_keys[self.selected_index]
        entry = BOSS_CODEX[sel_key]
        det_x, det_y, det_w, det_h = cx - 170, 195, 650, 410
        pygame.draw.rect(surf, (22, 28, 30), (det_x, det_y, det_w, det_h), border_radius=8)
        pygame.draw.rect(surf, RETRO_TERRA, (det_x, det_y, det_w, det_h), 2, border_radius=8)

        title_t = a.render_fit(['large', 'medium', 'small'], entry['name'], RETRO_CRIMSON, det_w - 48)
        surf.blit(title_t, (det_x + 24, det_y + 18))
        sec_t = a.render('small', entry['sector'], RETRO_CREAM)
        surf.blit(sec_t, (det_x + 24, det_y + 55))

        pygame.draw.line(surf, RETRO_TERRA, (det_x + 20, det_y + 88), (det_x + det_w - 20, det_y + 88), 1)

        s1 = a.render_fit(['small', 'tiny'], f"HULL HP: {entry['hp']}    SHIELD: {entry['shield']}    REWARD: {entry['score']} PTS", WHITE, det_w - 48)
        surf.blit(s1, (det_x + 24, det_y + 105))

        d_head = a.render('tiny', "INTELLIGENCE REPORT:", GREY)
        surf.blit(d_head, (det_x + 24, det_y + 150))
        desc_t = a.render_wrap('small', entry['desc'], WHITE, det_w - 48)
        surf.blit(desc_t, (det_x + 24, det_y + 175))

        t_head = a.render('tiny', "TACTICAL WEAKNESSES & STRATEGY:", GREY)
        surf.blit(t_head, (det_x + 24, det_y + 250))
        tac_t = a.render_wrap('small', entry['tactics'], RETRO_AMBER, det_w - 48)
        surf.blit(tac_t, (det_x + 24, det_y + 275))

    def _draw_shipyard_tab(self, surf, a):
        cx = W // 2
        x, y, w, h = cx - 480, 195, 960, 410
        pygame.draw.rect(surf, (20, 26, 28), (x, y, w, h), border_radius=8)

        t1 = a.render('large', "FLEET ARMAMENT & HULL SPECIFICATIONS", RETRO_AMBER)
        surf.blit(t1, (x + 24, y + 20))

        lines = [
            "• CLASSIC STRIKE: High-agility standard strike fighter with baseline vectoring.",
            "• CRIMSON TITAN: Reinforced alloy hull with aggressive forward missile payload.",
            "• VOID SHIFTER: Phase-shifted hull with reduced projectile collision profile.",
            "",
            "ARMAMENT COMPONENTS:",
            "• Laser Cannon Mk2: +5 Damage output per primary laser bolt.",
            "• Aegis Shield Array: +40 Maximum Energy Shield capacity.",
            "• Plasma Core Overdrive: Faster ship responsiveness & scroll speeds.",
            "• Seeker Missile Rack: Automatically launches homing ordnance every 5 primary shots.",
        ]
        for i, l in enumerate(lines):
            col = RETRO_CREAM if l.startswith("ARMAMENT") else WHITE
            t = a.render_fit(['small', 'tiny'], l, col, w - 48)
            surf.blit(t, (x + 24, y + 68 + i * 32))

    def _draw_achievements_tab(self, surf, a):
        cx = W // 2
        x, y, w, h = cx - 480, 195, 960, 410
        pygame.draw.rect(surf, (20, 26, 28), (x, y, w, h), border_radius=8)

        col_w = (w - 32) // 2
        row_h = 60
        for i, ach in enumerate(ACHIEVEMENTS[:12]):
            col_idx = i % 2
            row_idx = i // 2
            ax = x + 10 + col_idx * (col_w + 12)
            ay = y + 10 + row_idx * (row_h + 6)

            unlocked = ach['id'] in self.unlocked_achievements
            bg_col = (26, 38, 30) if unlocked else (24, 28, 30)
            border_col = RETRO_SAGE if unlocked else RETRO_MOSS

            rect = pygame.Rect(ax, ay, col_w, row_h)
            pygame.draw.rect(surf, bg_col, rect, border_radius=6)
            pygame.draw.rect(surf, border_col, rect, 1, border_radius=6)

            icon_t = a.render('large', ach['icon'], WHITE)
            surf.blit(icon_t, (rect.x + 12, rect.centery - icon_t.get_height() // 2))

            title_t = a.render('small', ach['title'], RETRO_AMBER if unlocked else WHITE)
            desc_t = a.render_fit(['tiny'], ach['desc'], RETRO_SAGE if unlocked else GREY, col_w - 120)
            surf.blit(title_t, (rect.x + 48, rect.y + 8))
            surf.blit(desc_t, (rect.x + 48, rect.y + 32))

            rew_t = a.render('tiny', f"+{ach['reward']} CR", RETRO_CREAM if unlocked else GREY)
            surf.blit(rew_t, (rect.right - rew_t.get_width() - 10, rect.centery - rew_t.get_height() // 2))
