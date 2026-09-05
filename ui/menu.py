"""
ui/menu.py
----------
Warm Retro Menu Interface for Space Impact — Remastered.
Designed with the curated retro color palette:
#dfa05d (Amber), #ac5045 (Terra), #658761 (Sage), #dcc9a9 (Cream), #b83a2d (Crimson), #4e6851 (Moss).
Guarantees 100% collision-free layout, generous breathing room under titles and labels,
prominent high score & credit badges, and properly working shipyard parts equipping.
"""
import pygame
import math

from core.settings import (W, H, TOTAL_SECTORS, BG, BLUE, CYAN, WHITE, GREY,
                            DGREY, YELLOW, GREEN, RED, GOLD, PURPLE, ORANGE,
                            RETRO_AMBER, RETRO_TERRA, RETRO_SAGE, RETRO_CREAM, RETRO_CRIMSON, RETRO_MOSS)
from core.assets import Assets
from systems.loadout import (SKINS, PART_CATEGORIES, DEFAULT_EQUIPPED_PARTS,
                             campaign_power, recommended_power)
from systems.story import SECTOR_STORIES
from ui.components import Button, Panel, draw_text_shadow, draw_glow_rect


class MainMenu:
    def __init__(self):
        self._screen = 'main'  # 'main', 'campaign', 'shop'
        cx = W // 2
        
        # Primary Game Modes
        self._btn_campaign    = Button(cx - 364, 310, 356, 74, "CAMPAIGN", color=RETRO_MOSS, subtext="STORY // 13 SECTORS", font_key='large')
        self._btn_endless     = Button(cx + 8,   310, 356, 74, "ENDLESS RUN", color=RETRO_MOSS, subtext="INFINITE WAVE SURGE", font_key='large')
        
        self._btn_boss_rush   = Button(cx - 364, 400, 232, 66, "BOSS RUSH", color=RETRO_TERRA, subtext="ARENA CLASH", font_key='medium')
        self._btn_survival    = Button(cx - 116, 400, 232, 66, "SURVIVAL", color=RETRO_SAGE, subtext="TIMED EXTRACTION", font_key='medium')
        self._btn_time_attack = Button(cx + 132, 400, 232, 66, "TIME ATTACK", color=RETRO_TERRA, subtext="SPEEDRUN HUNT", font_key='medium')

        # Challenge Preset Selector Row (56px tall for 100% text containment, with generous gap under label)
        self._difficulty = 'standard'
        dw = 172
        dy = 535
        self._btn_diff_standard   = Button(cx - 364, dy, dw, 56, "STANDARD",    color=RETRO_MOSS, font_key='small', subtext="1.0x REWARD")
        self._btn_diff_hardcore   = Button(cx - 182, dy, dw, 56, "HARDCORE",    color=RETRO_TERRA, font_key='small', subtext="+50% CREDITS")
        self._btn_diff_bullethell = Button(cx,       dy, dw, 56, "BULLET HELL", color=RETRO_CRIMSON, font_key='small', subtext="RING VOLLEYS")
        self._btn_diff_doubleboss = Button(cx + 182, dy, dw, 56, "DOUBLE BOSS", color=RETRO_TERRA, font_key='small', subtext="TWIN TITANS")

        # Bottom Command Bar
        bar_y = H - 90
        self._btn_settings = Button(cx - 450, bar_y, 210, 54, "SETTINGS", color=RETRO_MOSS, font_key='small')
        self._btn_codex    = Button(cx - 225, bar_y, 210, 54, "CODEX & LORE", color=RETRO_MOSS, font_key='small')
        self._btn_store    = Button(cx + 15,  bar_y, 210, 54, "SHIPYARD", color=RETRO_SAGE, font_key='small')
        self._btn_quit     = Button(cx + 240, bar_y, 210, 54, "EXIT GAME", color=RETRO_CRIMSON, hover_color=RETRO_TERRA, font_key='small')

        # Subscreen Navigation
        self._btn_back = Button(50, bar_y + 12, 160, 52, "< BACK", color=RETRO_MOSS, font_key='small')
        self._btn_play = Button(cx - 210, 730, 420, 60, "START MISSION", color=RETRO_SAGE, font_key='medium')
        self._btn_continue = None

        # Shipyard Controls (Placed strictly inside respective cards)
        self._skin_prev_btn   = Button(cx - 250, 410, 48, 48, "<", font_key='large', color=RETRO_MOSS)
        self._skin_next_btn   = Button(cx + 430, 410, 48, 48, ">", font_key='large', color=RETRO_MOSS)
        self._skin_action_btn = Button(cx - 185, 410, 595, 48, "EQUIP SKIN", color=RETRO_SAGE, font_key='medium')
        
        self._part_prev_btn   = Button(cx - 250, 675, 48, 48, "<", font_key='large', color=RETRO_MOSS)
        self._part_next_btn   = Button(cx + 430, 675, 48, 48, ">", font_key='large', color=RETRO_MOSS)
        self._part_action_btn = Button(cx - 185, 675, 595, 48, "INSTALL COMPONENT", color=RETRO_SAGE, font_key='medium')

        self._level_buttons = []
        self._category_buttons = []
        self._owned_skins = {'classic'}
        self._owned_parts = set(DEFAULT_EQUIPPED_PARTS.values())
        self._equipped_skin = 'classic'
        self._equipped_parts = dict(DEFAULT_EQUIPPED_PARTS)
        self._skin_index = 0
        self._selected_category_index = 0
        self._selected_part_indices = {cat['id']: 0 for cat in PART_CATEGORIES}
        self._unlocked_sector = 1
        self._completed_sector = 0
        self._selected_sector = 1
        self._tick = 0
        self._stars = None
        self._build_category_buttons()

    def set_starfield(self, starfield):
        self._stars = starfield

    def set_has_save(self, has_save):
        cx = W // 2
        y_offset = 0  # Initialize default offset

        if has_save:
            self._btn_continue = Button(cx - 364, 230, 728, 64, "RESUME CAMPAIGN", color=RETRO_SAGE, subtext="CONTINUE SAVED MISSION", font_key='medium')
        else:
            self._btn_continue = None
            y_offset = -15  # Slid up to take the exact spot of the Resume button

        # Update button vertical positions
        self._btn_campaign.rect.top    = 310 + y_offset
        self._btn_endless.rect.top     = 310 + y_offset
        self._btn_boss_rush.rect.top   = 398 + y_offset
        self._btn_survival.rect.top    = 398 + y_offset
        self._btn_time_attack.rect.top = 398 + y_offset

        # Update challenge selector vertical positions
        self._btn_diff_standard.rect.top   = 525 + y_offset
        self._btn_diff_hardcore.rect.top   = 525 + y_offset
        self._btn_diff_bullethell.rect.top = 525 + y_offset
        self._btn_diff_doubleboss.rect.top = 525 + y_offset

    def set_campaign_progress(self, unlocked_sector=1, completed_sector=0):
        self._unlocked_sector = max(1, min(TOTAL_SECTORS, int(unlocked_sector or 1)))
        self._completed_sector = max(0, min(TOTAL_SECTORS, int(completed_sector or 0)))
        if not hasattr(self, '_selected_sector') or self._selected_sector > self._unlocked_sector:
            self._selected_sector = self._unlocked_sector
        
        self._level_buttons = []
        cols = 7
        size = 84
        gap = 16
        start_x = W // 2 - (cols * size + (cols - 1) * gap) // 2
        start_y = 280

        for idx in range(TOTAL_SECTORS):
            row = idx // cols
            col = idx % cols
            sector = idx + 1
            x = start_x + col * (size + gap)
            y = start_y + row * (size + gap + 30)

            unlocked = sector <= self._unlocked_sector
            completed = sector <= self._completed_sector
            
            if completed:
                col_btn = RETRO_SAGE
            elif unlocked:
                col_btn = RETRO_MOSS
            else:
                col_btn = (28, 34, 36)

            btn = Button(x, y, size, size, str(sector), color=col_btn, font_key='large', radius=8)
            self._level_buttons.append((sector, unlocked, btn))

    def set_profile(self, owned_skins, equipped_skin, owned_parts, equipped_parts):
        self._owned_skins = set(owned_skins or {'classic'})
        self._equipped_skin = equipped_skin or 'classic'
        self._owned_parts = set(owned_parts or DEFAULT_EQUIPPED_PARTS.values())
        self._equipped_parts = dict(DEFAULT_EQUIPPED_PARTS)
        self._equipped_parts.update(equipped_parts or {})

    def _build_category_buttons(self):
        self._category_buttons = []
        cx = W // 2
        start_y = 240
        for i, cat in enumerate(PART_CATEGORIES):
            btn = Button(cx - 500, start_y + i * 58, 200, 48, cat['name'].upper(), color=RETRO_MOSS, font_key='small')
            self._category_buttons.append((cat['id'], btn))

    def update(self):
        self._tick += 1

    def handle_event(self, event):
        if self._screen == 'main':
            if self._btn_continue and self._btn_continue.handle_event(event):
                return 'continue'
            if self._btn_campaign.handle_event(event):
                self._screen = 'campaign'
                return None
            if self._btn_endless.handle_event(event):
                return 'endless'
            if self._btn_boss_rush.handle_event(event):
                return 'boss_rush'
            if self._btn_survival.handle_event(event):
                return 'survival'
            if self._btn_time_attack.handle_event(event):
                return 'time_attack'

            # Difficulty preset selectors
            if self._btn_diff_standard.handle_event(event):
                self._difficulty = 'standard'
            elif self._btn_diff_hardcore.handle_event(event):
                self._difficulty = 'hardcore'
            elif self._btn_diff_bullethell.handle_event(event):
                self._difficulty = 'bullet_hell'
            elif self._btn_diff_doubleboss.handle_event(event):
                self._difficulty = 'double_boss'

            if self._btn_settings.handle_event(event):
                return 'settings'
            if self._btn_codex.handle_event(event):
                return 'codex'
            if self._btn_store.handle_event(event):
                self._screen = 'shop'
                return None
            if self._btn_quit.handle_event(event):
                return 'quit'
            return None

        if self._btn_back.handle_event(event):
            self._screen = 'main'
            return None

        if self._screen == 'campaign':
            for sector, unlocked, btn in self._level_buttons:
                if unlocked and btn.handle_event(event):
                    if self._selected_sector == sector:
                        return ('campaign_level', sector)
                    self._selected_sector = sector
                    return None
            if self._btn_play.handle_event(event):
                sec = getattr(self, '_selected_sector', self._unlocked_sector)
                return ('campaign_level', sec)

        elif self._screen == 'shop':
            for i, (cat_id, btn) in enumerate(self._category_buttons):
                if btn.handle_event(event):
                    self._selected_category_index = i

            if self._skin_prev_btn.handle_event(event):
                self._skin_index = (self._skin_index - 1) % len(SKINS)
            if self._skin_next_btn.handle_event(event):
                self._skin_index = (self._skin_index + 1) % len(SKINS)

            cur_skin = SKINS[self._skin_index]
            if self._skin_action_btn.handle_event(event):
                if cur_skin['id'] in self._owned_skins:
                    return ('equip_skin', cur_skin['id'])
                else:
                    return ('buy_skin', cur_skin['id'])

            cur_cat = PART_CATEGORIES[self._selected_category_index]
            parts = cur_cat['parts']
            p_idx = self._selected_part_indices[cur_cat['id']]
            if self._part_prev_btn.handle_event(event):
                self._selected_part_indices[cur_cat['id']] = (p_idx - 1) % len(parts)
            if self._part_next_btn.handle_event(event):
                self._selected_part_indices[cur_cat['id']] = (p_idx + 1) % len(parts)

            cur_part = parts[self._selected_part_indices[cur_cat['id']]]
            if self._part_action_btn.handle_event(event):
                if cur_part['id'] in self._owned_parts:
                    return ('equip_part', cur_part['id'])
                else:
                    return ('buy_part', cur_part['id'])

        return None

    def draw(self, surf, high_score=0, credits=0):
        a = Assets()

        # Warm Retro Header Logo with generous spacing
        t_glow = a.render_glow('title', "SPACE IMPACT", RETRO_AMBER, glow_color=RETRO_TERRA, glow_radius=3)
        surf.blit(t_glow, (W // 2 - t_glow.get_width() // 2, 35))
        
        # Clean spacing under the main title
        sub = a.render('small', "— RETRO TACTICAL REMASTER —", RETRO_CREAM)
        surf.blit(sub, (W // 2 - sub.get_width() // 2, 142))

        # Top Right Badges (High Score & Credits - Highly visible and prominent)
        badge_p = Panel(W - 400, 32, 360, 96, color=(24, 30, 32), border_color=RETRO_MOSS, alpha=235)
        badge_p.draw(surf)
        hs_t = a.render('small', f"HIGH SCORE:  {high_score:,}", RETRO_CREAM)
        cr_t = a.render('large', f"CREDITS:  {credits:,} CR", RETRO_AMBER)
        surf.blit(hs_t, (W - 380, 44))
        surf.blit(cr_t, (W - 380, 72))

        if self._screen == 'main':
            self._draw_main(surf, a)
        elif self._screen == 'campaign':
            self._draw_campaign(surf, a)
        elif self._screen == 'shop':
            self._draw_shop(surf, a, credits)

    def _draw_main(self, surf, a):
        cx = W // 2
        
        # Match panel top border tightly to the top button (20px padding)
        y_off = 0 if self._btn_continue else -15        
        panel_y = 240 if not self._btn_continue else 190
        panel_h = 500 if not self._btn_continue else 560

        hub_panel = Panel(cx - 410, panel_y, 820, panel_h, color=(24, 30, 32), border_color=RETRO_MOSS, alpha=235)
        hub_panel.draw(surf)

        if self._btn_continue:
            self._btn_continue.draw(surf)

        self._btn_campaign.draw(surf)
        self._btn_endless.draw(surf)
        self._btn_boss_rush.draw(surf)
        self._btn_survival.draw(surf)
        self._btn_time_attack.draw(surf)

        # Challenge Presets Section Frame with generous breathing room
        pygame.draw.line(surf, RETRO_MOSS, (cx - 364, 478 + y_off), (cx + 364, 478+ y_off), 1)
        mod_label = a.render('small', "CHALLENGE MODIFIER PRESET:", RETRO_CREAM)
        surf.blit(mod_label, (cx - 364, 490 + y_off))

        self._btn_diff_standard.active   = (self._difficulty == 'standard')
        self._btn_diff_hardcore.active   = (self._difficulty == 'hardcore')
        self._btn_diff_bullethell.active = (self._difficulty == 'bullet_hell')
        self._btn_diff_doubleboss.active = (self._difficulty == 'double_boss')

        self._btn_diff_standard.draw(surf)
        self._btn_diff_hardcore.draw(surf)
        self._btn_diff_bullethell.draw(surf)
        self._btn_diff_doubleboss.draw(surf)

        # Challenge Modifier Intel Card (explains exactly what each preset does)
        preset_info = {
            'standard': {
                'title': "STANDARD PROTOCOL — 1.0X REWARDS",
                'desc': "Balanced simulation. Standard enemy hull durability, default swarm speed, single sector titan.",
                'color': RETRO_SAGE,
            },
            'hardcore': {
                'title': "HARDCORE SPEC — +50% BONUS CREDITS (1.5X)",
                'desc': "High-intensity threat: +30% enemy HP, +15% velocity, +25% spawn rate, +40% boss resilience.",
                'color': RETRO_TERRA,
            },
            'bullet_hell': {
                'title': "BULLET HELL DENSITY — +50% BONUS CREDITS (1.5X)",
                'desc': "Heavy barrage volume: Enemies fire denser ring volleys with +45% faster swarm rate.",
                'color': RETRO_CRIMSON,
            },
            'double_boss': {
                'title': "DOUBLE BOSS SURGE — +25% BONUS CREDITS (1.25X)",
                'desc': "Twin Titans Protocol: Spawns two sector bosses simultaneously on split upper & lower flight lanes. Defeat both to clear.",
                'color': RETRO_AMBER,
            },
        }
        info = preset_info.get(self._difficulty, preset_info['standard'])
        info_panel = pygame.Surface((728, 104), pygame.SRCALPHA)
        info_panel.fill((18, 24, 26, 200))
        pygame.draw.rect(info_panel, (*info['color'], 180), (0, 0, 728, 104), 1, border_radius=6)
        t_header = a.render('small', info['title'], info['color'])
        t_body = a.render_wrap('tiny', info['desc'], WHITE, 700)
        info_panel.blit(t_header, (14, 10))
        info_panel.blit(t_body, (14, 38))
        surf.blit(info_panel, (cx - 364, 595 + y_off))

        # Bottom Command Bar
        bot_panel = Panel(cx - 470, H - 105, 940, 80, color=(24, 30, 32), border_color=RETRO_MOSS, alpha=235)
        bot_panel.draw(surf)
        self._btn_settings.draw(surf)
        self._btn_codex.draw(surf)
        self._btn_store.draw(surf)
        self._btn_quit.draw(surf)

    def _draw_campaign(self, surf, a):
        cx = W // 2
        p = Panel(cx - 520, 180, 1040, 770, color=(24, 30, 32), border_color=RETRO_MOSS, alpha=235)
        p.draw(surf)

        t = a.render('large', "TACTICAL SECTOR CAMPAIGN", RETRO_AMBER)
        surf.blit(t, (cx - t.get_width() // 2, 205))
        sub = a.render('small', "SELECT AN UNLOCKED SECTOR TO VIEW INTEL AND DEPLOY", RETRO_CREAM)
        surf.blit(sub, (cx - sub.get_width() // 2, 245))

        for sector, unlocked, btn in self._level_buttons:
            if sector == self._selected_sector:
                pygame.draw.rect(surf, RETRO_AMBER, btn.rect.inflate(10, 10), 3, border_radius=btn.radius + 4)
                pygame.draw.rect(surf, RETRO_CREAM, btn.rect.inflate(4, 4), 1, border_radius=btn.radius + 2)
            btn.draw(surf)
            lbl_col = RETRO_SAGE if sector <= self._completed_sector else (RETRO_CREAM if unlocked else GREY)
            status = "CLEAR" if sector <= self._completed_sector else ("READY" if unlocked else "LOCK")
            st_t = a.render('tiny', status, lbl_col)
            surf.blit(st_t, (btn.rect.centerx - st_t.get_width() // 2, btn.rect.bottom + 4))

        # Selected Sector Briefing Card
        card_y = 550
        card_h = 285
        b_panel = Panel(cx - 460, card_y, 920, card_h, color=(18, 24, 26), border_color=RETRO_MOSS, alpha=230)
        b_panel.draw(surf)

        st = SECTOR_STORIES.get(self._selected_sector, {})
        sec_title = st.get('title', f"SECTOR {self._selected_sector}")
        sec_sub = st.get('subtitle', "")
        boss_name = st.get('boss_name', "UNKNOWN THREAT")
        boss_desc = st.get('boss_desc', "")

        t_st = a.render('medium', sec_title, RETRO_AMBER)
        surf.blit(t_st, (cx - t_st.get_width() // 2, card_y + 18))
        if sec_sub:
            t_sub = a.render('small', f"— {sec_sub} —", RETRO_CREAM)
            surf.blit(t_sub, (cx - t_sub.get_width() // 2, card_y + 48))

        pygame.draw.line(surf, RETRO_MOSS, (cx - 380, card_y + 78), (cx + 380, card_y + 78), 1)

        t_boss = a.render_fit(['small', 'tiny'], f"PRIMARY TARGET: {boss_name.upper()}  —  {boss_desc}", RETRO_CRIMSON, 860)
        surf.blit(t_boss, (cx - t_boss.get_width() // 2, card_y + 92))

        power = campaign_power(self._equipped_parts)
        rec = recommended_power(self._selected_sector)
        pow_col = RETRO_SAGE if power >= rec else RETRO_TERRA
        t_pow = a.render('small', f"FLEET POWER: {power}   |   RECOMMENDED: {rec}", pow_col)
        surf.blit(t_pow, (cx - t_pow.get_width() // 2, card_y + 124))

        status_text = "STATUS: SECTOR PREVIOUSLY CLEARED (REPLAY AVAILABLE)" if self._selected_sector <= self._completed_sector else "STATUS: MISSION ACTIVE & READY FOR LAUNCH"
        status_col = RETRO_SAGE if self._selected_sector <= self._completed_sector else RETRO_CREAM
        t_stat = a.render('tiny', status_text, status_col)
        surf.blit(t_stat, (cx - t_stat.get_width() // 2, card_y + 155))

        self._btn_play.rect = pygame.Rect(cx - 210, card_y + 190, 420, 64)
        self._btn_play.text = f"START MISSION  (SECTOR {self._selected_sector})"
        self._btn_play.draw(surf)

        self._btn_back.draw(surf)

    def _draw_shop(self, surf, a, credits):
        cx = W // 2
        # Main Outer Panel for Shipyard
        p = Panel(cx - 530, 160, 1060, 720, color=(24, 30, 32), border_color=RETRO_MOSS, alpha=235)
        p.draw(surf)

        t = a.render('large', "SPACEPORT SHIPYARD & WEAPON TECH", RETRO_AMBER)
        surf.blit(t, (cx - 500, 185))

        for cat_id, btn in self._category_buttons:
            btn.active = (PART_CATEGORIES[self._selected_category_index]['id'] == cat_id)
            btn.draw(surf)

        cur_skin = SKINS[self._skin_index]
        cur_cat = PART_CATEGORIES[self._selected_category_index]
        cur_part = cur_cat['parts'][self._selected_part_indices[cur_cat['id']]]

        # Skin Area Card (y = 240..482)
        skin_card = Panel(cx - 270, 240, 770, 235, color=(20, 26, 28), border_color=RETRO_MOSS, alpha=225)
        skin_card.draw(surf)
        s_title = a.render('medium', f"HULL SKIN: {cur_skin['name'].upper()}", RETRO_AMBER if cur_skin['id'] in self._owned_skins else RETRO_CREAM)
        surf.blit(s_title, (cx - 250, 255))
        s_desc = a.render('small', cur_skin['desc'], GREY)
        surf.blit(s_desc, (cx - 250, 290))

        self._skin_prev_btn.draw(surf)
        self._skin_next_btn.draw(surf)
        
        is_equipped_skin = (self._equipped_skin == cur_skin['id'])
        is_owned_skin = (cur_skin['id'] in self._owned_skins)
        
        if is_equipped_skin:
            self._skin_action_btn.text = "EQUIPPED"
            self._skin_action_btn.color = RETRO_SAGE
        elif is_owned_skin:
            self._skin_action_btn.text = "EQUIP SKIN"
            self._skin_action_btn.color = RETRO_MOSS
        else:
            self._skin_action_btn.text = f"BUY HULL ({cur_skin['cost']:,} CR)"
            self._skin_action_btn.color = RETRO_AMBER
        self._skin_action_btn.draw(surf)

        # Part Area Card (y = 495..730)
        part_card = Panel(cx - 270, 495, 770, 235, color=(20, 26, 28), border_color=RETRO_MOSS, alpha=225)
        part_card.draw(surf)
        p_title = a.render('medium', f"{cur_cat['name'].upper()}: {cur_part['name'].upper()}", RETRO_AMBER)
        surf.blit(p_title, (cx - 250, 510))
        p_desc = a.render('small', cur_part['desc'], GREY)
        surf.blit(p_desc, (cx - 250, 545))

        self._part_prev_btn.draw(surf)
        self._part_next_btn.draw(surf)

        is_equipped_part = (self._equipped_parts.get(cur_cat['id']) == cur_part['id'])
        is_owned_part = (cur_part['id'] in self._owned_parts)

        if is_equipped_part:
            self._part_action_btn.text = "EQUIPPED"
            self._part_action_btn.color = RETRO_SAGE
        elif is_owned_part:
            self._part_action_btn.text = "INSTALL COMPONENT"
            self._part_action_btn.color = RETRO_MOSS
        else:
            self._part_action_btn.text = f"BUY COMPONENT ({cur_part['cost']:,} CR)"
            self._part_action_btn.color = RETRO_AMBER
        self._part_action_btn.draw(surf)

        # Bottom Return Button
        self._btn_back.rect.topleft = (cx - 80, 810)
        self._btn_back.draw(surf)
