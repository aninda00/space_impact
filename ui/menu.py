import pygame
import math

from core.settings import W, H, TOTAL_SECTORS, BG, BLUE, CYAN, WHITE, GREY, YELLOW, GREEN
from core.assets import Assets
from systems.loadout import (SKINS, PART_CATEGORIES, DEFAULT_EQUIPPED_PARTS,
                             campaign_power, recommended_power)
from ui.components import Button, Panel, draw_text_shadow


class MainMenu:
    def __init__(self):
        self._screen = 'main'
        self._btn_campaign = Button(W // 2 - 190, H // 2 - 20, 380, 70, "CAMPAIGN", color=(30, 120, 255))
        self._btn_endless = Button(W // 2 - 190, H // 2 + 75, 380, 70, "ENDLESS", color=(170, 70, 255))
        self._btn_boss_rush = Button(W // 2 - 360, H // 2 + 170, 220, 64, "BOSS RUSH", color=(220, 60, 70), font_key='medium')
        self._btn_survival = Button(W // 2 - 110, H // 2 + 170, 220, 64, "SURVIVAL", color=(30, 155, 95), font_key='medium')
        self._btn_time_attack = Button(W // 2 + 140, H // 2 + 170, 220, 64, "TIME ATTACK", color=(240, 145, 30), font_key='medium')
        self._btn_play = Button(W // 2 - 340, H // 2 + 20, 320, 62, "NEW CAMPAIGN", color=(30, 120, 255))
        self._btn_continue = None
        self._btn_store = Button(W - 284, H - 98, 240, 58, "SHIPYARD", color=(28, 98, 168), font_key='small')
        self._btn_back = Button(40, H - 110, 180, 52, "BACK", color=(40, 40, 80), font_key='small')
        self._btn_quit = Button(W // 2 - 160, H // 2 + 295, 320, 55, "EXIT", color=(60, 25, 25), hover_color=(160, 40, 40))

        self._skin_prev_btn = Button(W // 2 + 150, 520, 56, 48, "<", font_key='large')
        self._skin_next_btn = Button(W // 2 + 704, 520, 56, 48, ">", font_key='large')
        self._skin_action_btn = Button(W // 2 + 280, 596, 320, 58, "BUY", color=(40, 130, 70))
        self._part_prev_btn = Button(W // 2 + 150, 792, 56, 48, "<", font_key='large')
        self._part_next_btn = Button(W // 2 + 704, 792, 56, 48, ">", font_key='large')
        self._part_action_btn = Button(W // 2 + 280, 888, 320, 58, "BUY", color=(40, 130, 70))

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
        self._tick = 0
        self._stars = None
        self._btn_quit.rect.topleft = (W // 2 - 160, H // 2 + 295)
        self._shop_layout = {}
        self._profile_signature = None
        self._build_category_buttons()

    def set_starfield(self, starfield):
        self._stars = starfield

    def set_has_save(self, has_save):
        if has_save and self._btn_continue is None:
            self._btn_continue = Button(W // 2 + 20, H // 2 + 20, 320, 62, "CONTINUE", color=(30, 140, 80))
        elif not has_save:
            self._btn_continue = None

    def set_campaign_progress(self, unlocked_sector=1, completed_sector=0):
        unlocked_sector = max(1, min(TOTAL_SECTORS, int(unlocked_sector or 1)))
        completed_sector = max(0, min(TOTAL_SECTORS, int(completed_sector or 0)))
        if self._level_buttons and unlocked_sector == self._unlocked_sector and completed_sector == self._completed_sector:
            return
        self._unlocked_sector = unlocked_sector
        self._completed_sector = completed_sector
        self._level_buttons = []
        cols = 7
        size = 92
        gap = 18
        start_x = W // 2 - (cols * size + (cols - 1) * gap) // 2
        start_y = H // 2 + 150
        for idx in range(TOTAL_SECTORS):
            row = idx // cols
            col = idx % cols
            sector = idx + 1
            x = start_x + col * (size + gap)
            y = start_y + row * (size + gap)
            unlocked = sector <= self._unlocked_sector
            completed = sector <= self._completed_sector
            color = (30, 120, 255) if unlocked else (42, 46, 66)
            if completed:
                color = (30, 140, 80)
            text_color = WHITE if unlocked else GREY
            self._level_buttons.append((sector, unlocked, Button(x, y, size, size, str(sector), color=color, text_color=text_color, font_key='large', radius=8)))

    def set_profile(self, owned_skins, equipped_skin, owned_parts, equipped_parts):
        new_signature = (
            tuple(sorted(owned_skins or {'classic'})),
            equipped_skin or 'classic',
            tuple(sorted(owned_parts or DEFAULT_EQUIPPED_PARTS.values())),
            tuple(sorted((equipped_parts or {}).items())),
        )
        reset_browse = self._profile_signature != new_signature and self._screen != 'shop'
        self._profile_signature = new_signature
        self._owned_skins = set(owned_skins or {'classic'})
        self._owned_parts = set(owned_parts or DEFAULT_EQUIPPED_PARTS.values())
        self._equipped_skin = equipped_skin or 'classic'
        self._equipped_parts = dict(DEFAULT_EQUIPPED_PARTS)
        self._equipped_parts.update(equipped_parts or {})
        if reset_browse:
            self._skin_index = next((i for i, skin in enumerate(SKINS) if skin['id'] == self._equipped_skin), 0)
            for category in PART_CATEGORIES:
                equipped = self._equipped_parts.get(category['id'], category['parts'][0]['id'])
                self._selected_part_indices[category['id']] = next((i for i, part in enumerate(category['parts']) if part['id'] == equipped), 0)
        if not self._category_buttons:
            self._build_category_buttons()

    def _build_category_buttons(self):
        self._category_buttons = []
        for idx, category in enumerate(PART_CATEGORIES):
            self._category_buttons.append((category['id'], Button(0, 0, 250, 62, category['name'].upper(), color=(38, 54, 96), font_key='small')))

    def _layout_shop(self):
        page = pygame.Rect(60, 300, W - 140, H - 350)
        header_h = 154
        footer_h = 82
        gutter = 34
        left_w = 560
        header_rect = pygame.Rect(page.x + 30, page.y + 22, page.w - 60, header_h - 22)
        content_top = header_rect.bottom + 24
        content_bottom = page.bottom - footer_h
        right_x = page.x + left_w + gutter
        right_w = page.right - right_x - 28
        category_area = pygame.Rect(page.x + 30, content_top + 34, left_w - 60, content_bottom - content_top - 42)
        cols = 2
        rows = 5
        h_gap = 26
        v_gap = 18
        btn_w = (category_area.w - h_gap) // cols
        btn_h = (category_area.h - v_gap * (rows - 1)) // rows
        for idx, (_, button) in enumerate(self._category_buttons):
            row = idx // cols
            col = idx % cols
            x = category_area.x + col * (btn_w + h_gap)
            y = category_area.y + row * (btn_h + v_gap)
            button.rect.topleft = (x, y)
            button.rect.size = (btn_w, btn_h)

        skin_panel = pygame.Rect(right_x, content_top, right_w, 248)
        part_panel = pygame.Rect(right_x, skin_panel.bottom + 28, right_w, page.bottom - skin_panel.bottom - 64)

        arrow_size = (58, 52)
        self._skin_prev_btn.rect.size = arrow_size
        self._skin_next_btn.rect.size = arrow_size
        self._part_prev_btn.rect.size = arrow_size
        self._part_next_btn.rect.size = arrow_size

        self._skin_prev_btn.rect.topleft = (skin_panel.x + 22, skin_panel.y + 110)
        self._skin_next_btn.rect.topright = (skin_panel.right - 22, skin_panel.y + 110)
        self._part_prev_btn.rect.topleft = (part_panel.x + 22, part_panel.y + 98)
        self._part_next_btn.rect.topright = (part_panel.right - 22, part_panel.y + 98)

        action_w, action_h = 210, 56
        self._skin_action_btn.rect.size = (action_w, action_h)
        self._part_action_btn.rect.size = (action_w, action_h)
        self._skin_action_btn.rect.bottomright = (skin_panel.right - 30, skin_panel.bottom - 16)
        self._part_action_btn.rect.bottomright = (part_panel.right - 30, part_panel.bottom - 14)

        self._btn_back.rect.topleft = (page.x + 30, page.bottom - self._btn_back.rect.height - 14)

        self._shop_layout = {
            'page': page,
            'header_rect': header_rect,
            'content_top': content_top,
            'content_bottom': content_bottom,
            'category_area': category_area,
            'skin_panel': skin_panel,
            'part_panel': part_panel,
            'right_x': right_x,
            'right_w': right_w,
        }

    def handle_event(self, event):
        if self._screen == 'main':
            if self._btn_campaign.handle_event(event):
                self._screen = 'campaign'
            if self._btn_endless.handle_event(event):
                return 'endless'
            if self._btn_boss_rush.handle_event(event):
                return 'boss_rush'
            if self._btn_survival.handle_event(event):
                return 'survival'
            if self._btn_time_attack.handle_event(event):
                return 'time_attack'
            if self._btn_quit.handle_event(event):
                return 'quit'
            return None

        if self._btn_back.handle_event(event):
            self._screen = 'campaign' if self._screen == 'shop' else 'main'
            return None

        if self._screen == 'campaign':
            if self._btn_play.handle_event(event):
                return 'play'
            if self._btn_continue and self._btn_continue.handle_event(event):
                return 'continue'
            if self._btn_store.handle_event(event):
                self._screen = 'shop'
                return None
            for sector, unlocked, button in self._level_buttons:
                if unlocked and button.handle_event(event):
                    return ('sector', sector)
            return None

        if self._screen == 'shop':
            self._layout_shop()
            if self._shipyard_arrow_clicked(event, self._skin_prev_btn):
                self._skin_index = (self._skin_index - 1) % len(SKINS)
            if self._shipyard_arrow_clicked(event, self._skin_next_btn):
                self._skin_index = (self._skin_index + 1) % len(SKINS)
            skin = SKINS[self._skin_index]
            if self._skin_action_btn.handle_event(event):
                return self._action_result('skin', skin['id'], skin['cost'], skin['id'] in self._owned_skins, skin['id'] == self._equipped_skin)
            for idx, (category_id, button) in enumerate(self._category_buttons):
                if button.handle_event(event):
                    self._selected_category_index = idx
            category = PART_CATEGORIES[self._selected_category_index]
            category_id = category['id']
            if self._shipyard_arrow_clicked(event, self._part_prev_btn):
                self._selected_part_indices[category_id] = (self._selected_part_indices[category_id] - 1) % len(category['parts'])
            if self._shipyard_arrow_clicked(event, self._part_next_btn):
                self._selected_part_indices[category_id] = (self._selected_part_indices[category_id] + 1) % len(category['parts'])
            part = category['parts'][self._selected_part_indices[category_id]]
            owned = part['id'] in self._owned_parts
            equipped = self._equipped_parts.get(category_id, category['parts'][0]['id']) == part['id']
            if self._part_action_btn.handle_event(event):
                return self._action_result('part', part['id'], part['cost'], owned, equipped)
        return None

    def _shipyard_arrow_clicked(self, event, button):
        if event.type == pygame.MOUSEMOTION:
            button.hovered = button.rect.collidepoint(event.pos)
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and getattr(event, 'button', 0) == 1:
            if button.rect.collidepoint(event.pos):
                button.hovered = True
                return True
        if event.type == pygame.MOUSEBUTTONUP and getattr(event, 'button', 0) == 1:
            button.hovered = button.rect.collidepoint(event.pos)
        return False

    def _action_result(self, kind, item_id, cost, owned, equipped):
        if equipped:
            return None
        if owned:
            return (f'equip_{kind}', item_id)
        return (f'buy_{kind}', item_id)

    def update(self):
        self._tick += 1

    def draw(self, surf, high_score=0, credits=0):
        a = Assets()
        surf.fill(BG)
        if self._stars:
            self._stars.update()
            self._stars.draw(surf)

        title_panel = Panel(W // 2 - 520, 80, 1040, 190, alpha=210)
        title_panel.draw(surf)
        t1 = a.render_fit(['title', 'huge'], "SPACE IMPACT", CYAN, 980)
        t2 = a.render('large', "REMASTERED", WHITE)
        draw_text_shadow(surf, t1, (W // 2 - t1.get_width() // 2, 100), offset=(3, 3))
        draw_text_shadow(surf, t2, (W // 2 - t2.get_width() // 2, 210))

        if self._screen == 'main':
            self._draw_main(surf, a)
        elif self._screen == 'campaign':
            self._draw_campaign(surf, a, high_score, credits)
        else:
            self._draw_shop(surf, a, credits)

        v = a.render('tiny', "v1.3.0", GREY)
        surf.blit(v, (W - v.get_width() - 14, H - 26))

    def _draw_main(self, surf, a):
        cp = Panel(W // 2 - 430, H // 2 - 115, 860, 390, alpha=175)
        cp.draw(surf)
        title = a.render('medium', "SELECT MODE", WHITE)
        draw_text_shadow(surf, title, (W // 2 - title.get_width() // 2, H // 2 - 96))
        self._btn_campaign.draw(surf)
        self._btn_endless.draw(surf)
        self._btn_boss_rush.draw(surf)
        self._btn_survival.draw(surf)
        self._btn_time_attack.draw(surf)
        self._btn_quit.draw(surf)

    def _draw_campaign(self, surf, a, high_score, credits):
        panel = Panel(W // 2 - 610, H // 2 - 150, 1220, 520, alpha=182)
        panel.draw(surf)
        ctrl = a.render('medium', "CAMPAIGN", WHITE)
        c1 = a.render_fit(['medium', 'small'], "Scroll Wheel - Move up / down", WHITE, 960)
        c2 = a.render_fit(['medium', 'small', 'tiny'], "Campaign uses shipyard parts. No mid-wave upgrade picks.", WHITE, 960)
        draw_text_shadow(surf, ctrl, (W // 2 - ctrl.get_width() // 2, H // 2 - 135))
        draw_text_shadow(surf, c1, (W // 2 - c1.get_width() // 2, H // 2 - 96))
        draw_text_shadow(surf, c2, (W // 2 - c2.get_width() // 2, H // 2 - 60))
        ship_power = campaign_power(self._equipped_parts)
        rec_sector = max(1, min(TOTAL_SECTORS, self._unlocked_sector))
        rec_power = recommended_power(rec_sector)
        power_col = GREEN if ship_power >= rec_power else YELLOW
        power_text = a.render_fit(
            ['medium', 'small'],
            f"SHIP POWER  {ship_power}   RECOMMENDED FOR SECTOR {rec_sector}: {rec_power}",
            power_col,
            960,
        )
        draw_text_shadow(surf, power_text, (W // 2 - power_text.get_width() // 2, H // 2 - 24))

        if self._btn_continue:
            self._btn_play.rect.topleft = (W // 2 - 340, H // 2 + 20)
            self._btn_continue.rect.topleft = (W // 2 + 20, H // 2 + 20)
        else:
            self._btn_play.rect.topleft = (W // 2 - 160, H // 2 + 20)
        self._btn_play.draw(surf)
        if self._btn_continue:
            self._btn_continue.draw(surf)
        self._btn_store.draw(surf)

        label = a.render('small', "SECTOR SELECT", WHITE)
        draw_text_shadow(surf, label, (W // 2 - label.get_width() // 2, H // 2 + 100))
        for sector, unlocked, button in self._level_buttons:
            completed = sector <= self._completed_sector
            if completed:
                button.color = (30, 140, 80)
            elif unlocked:
                button.color = (30, 120, 255)
            else:
                button.color = (42, 46, 66)
            if unlocked and not completed and campaign_power(self._equipped_parts) < recommended_power(sector):
                button.color = (170, 120, 35)
            button.hover_color = tuple(min(255, c + 35) for c in button.color)
            button.draw(surf)
            if completed:
                mark = a.render('small', "OK", GREEN)
                draw_text_shadow(surf, mark, (button.rect.centerx - mark.get_width() // 2, button.rect.bottom - 30))
            elif not unlocked:
                lock = a.render('small', "X", WHITE)
                draw_text_shadow(surf, lock, (button.rect.centerx - lock.get_width() // 2, button.rect.bottom - 30))

        self._btn_back.draw(surf)
        self._draw_stats(surf, a, high_score, credits)

    def _draw_shop(self, surf, a, credits):
        self._layout_shop()
        page_rect = self._shop_layout['page']
        page = Panel(page_rect.x, page_rect.y, page_rect.w, page_rect.h, alpha=188)
        page.draw(surf)
        header_rect = self._shop_layout['header_rect']
        heading = a.render('large', "SHIPYARD", WHITE)
        sub = a.render_fit(['medium', 'small'], "Buy campaign-only parts and equip a permanent loadout before launch.", WHITE, page_rect.w - 240)
        credits_text = a.render('medium', f"CREDITS  {credits:06d}", (255, 220, 90))
        draw_text_shadow(surf, heading, (header_rect.x, header_rect.y))
        draw_text_shadow(surf, sub, (header_rect.x, header_rect.y + 48))
        credit_badge = pygame.Rect(header_rect.right - credits_text.get_width() - 28, header_rect.y + 4, credits_text.get_width() + 28, credits_text.get_height() + 18)
        badge = pygame.Surface(credit_badge.size, pygame.SRCALPHA)
        pygame.draw.rect(badge, (32, 24, 6, 220), badge.get_rect(), border_radius=10)
        pygame.draw.rect(badge, (255, 210, 70, 200), badge.get_rect(), 2, border_radius=10)
        surf.blit(badge, credit_badge.topleft)
        draw_text_shadow(surf, credits_text, (credit_badge.x + 14, credit_badge.y + 7), shadow=(52, 28, 0), offset=(2, 2))

        skin_rect = self._shop_layout['skin_panel']
        skin_panel = Panel(skin_rect.x, skin_rect.y, skin_rect.w, skin_rect.h, alpha=230)
        skin_panel.draw(surf)
        skin = SKINS[self._skin_index]
        preview_rect = pygame.Rect(skin_rect.x + 88, skin_rect.y + 88, 118, 88)
        self._draw_ship_preview(surf, skin, preview_rect)
        skin_title_x = preview_rect.right + 22
        skin_text_w = self._skin_action_btn.rect.left - skin_title_x - 28
        draw_text_shadow(surf, a.render('small', "SHIP SKIN", CYAN), (skin_rect.x + 24, skin_rect.y + 24))
        draw_text_shadow(surf, a.render_fit(['large', 'medium'], skin['name'], WHITE, skin_text_w), (skin_title_x, skin_rect.y + 84))
        draw_text_shadow(surf, a.render_fit(['small', 'tiny'], f"MODEL  {self._skin_index + 1} / {len(SKINS)}", YELLOW, 180), (skin_title_x, skin_rect.y + 130))
        draw_text_shadow(surf, a.render_fit(['medium', 'small'], skin['desc'], GREY, skin_text_w), (skin_title_x, skin_rect.y + 164))
        self._skin_prev_btn.color = (55, 155, 255)
        self._skin_next_btn.color = (55, 155, 255)
        self._skin_prev_btn.hover_color = (80, 175, 255)
        self._skin_next_btn.hover_color = (80, 175, 255)
        self._draw_arrow_button(surf, self._skin_prev_btn, 'left')
        self._draw_arrow_button(surf, self._skin_next_btn, 'right')
        self._style_action_button(self._skin_action_btn, skin['id'] in self._owned_skins, skin['id'] == self._equipped_skin)
        self._skin_action_btn.text = self._item_action_text(skin['id'] in self._owned_skins, skin['id'] == self._equipped_skin, skin['cost'])
        self._skin_action_btn.draw(surf)

        left_title = a.render('small', "PART CATEGORIES", WHITE)
        draw_text_shadow(surf, left_title, (self._shop_layout['category_area'].x, self._shop_layout['content_top']))
        for idx, (category_id, button) in enumerate(self._category_buttons):
            category = PART_CATEGORIES[idx]
            selected = idx == self._selected_category_index
            if selected:
                button.color = CYAN
            else:
                button.color = (38, 54, 96)
            button.hover_color = tuple(min(255, c + 30) for c in button.color)
            self._draw_category_button(surf, a, button, category)

        category = PART_CATEGORIES[self._selected_category_index]
        category_id = category['id']
        part = category['parts'][self._selected_part_indices[category_id]]
        owned = part['id'] in self._owned_parts
        equipped = self._equipped_parts.get(category_id, category['parts'][0]['id']) == part['id']

        part_rect = self._shop_layout['part_panel']
        part_panel = Panel(part_rect.x, part_rect.y, part_rect.w, part_rect.h, alpha=230)
        part_panel.draw(surf)
        icon_rect = pygame.Rect(part_rect.x + 92, part_rect.y + 90, 110, 110)
        self._draw_category_icon(surf, category['id'], icon_rect)
        part_title_x = icon_rect.right + 22
        part_text_w = max(260, self._part_action_btn.rect.left - part_title_x - 36)
        draw_text_shadow(surf, a.render('small', category['name'].upper(), CYAN), (part_rect.x + 24, part_rect.y + 24))
        draw_text_shadow(surf, a.render_fit(['large', 'medium'], part['name'], WHITE, part_text_w), (part_title_x, part_rect.y + 84))
        draw_text_shadow(surf, a.render_fit(['small', 'tiny'], f"ITEM  {self._selected_part_indices[category_id] + 1} / {len(category['parts'])}", YELLOW, 180), (part_title_x, part_rect.y + 130))
        draw_text_shadow(surf, a.render_fit(['medium', 'small'], part['desc'], GREY, part_text_w), (part_title_x, part_rect.y + 156))
        draw_text_shadow(surf, a.render_fit(['medium', 'small'], self._stats_text(part['stats']), WHITE, part_text_w), (part_title_x, part_rect.y + 192))
        self._part_prev_btn.color = (55, 155, 255)
        self._part_next_btn.color = (55, 155, 255)
        self._part_prev_btn.hover_color = (80, 175, 255)
        self._part_next_btn.hover_color = (80, 175, 255)
        self._draw_arrow_button(surf, self._part_prev_btn, 'left')
        self._draw_arrow_button(surf, self._part_next_btn, 'right')
        self._style_action_button(self._part_action_btn, owned, equipped)
        self._part_action_btn.text = self._item_action_text(owned, equipped, part['cost'])
        self._part_action_btn.draw(surf)

        self._btn_back.draw(surf)

    def _item_action_text(self, owned, equipped, cost):
        if equipped:
            return "EQUIPPED"
        if owned:
            return "EQUIP"
        return f"BUY  {cost}"

    def _draw_ship_preview(self, surf, skin, rect):
        colors = skin['colors']
        frame = pygame.Rect(rect)
        pygame.draw.rect(surf, (14, 20, 40), frame, border_radius=12)
        pygame.draw.rect(surf, (70, 110, 190), frame, 2, border_radius=12)
        ship = pygame.Surface((rect.w - 16, rect.h - 18), pygame.SRCALPHA)
        w, h = ship.get_size()
        pygame.draw.polygon(ship, colors['body'], [(8, h // 2 - 10), (w - 28, h // 2 - 10), (w - 10, h // 2), (w - 28, h // 2 + 10), (8, h // 2 + 10)])
        pygame.draw.polygon(ship, colors['nose'], [(w - 28, h // 2 - 10), (w - 2, h // 2), (w - 28, h // 2 + 10)])
        pygame.draw.polygon(ship, colors['wing'], [(18, h // 2 - 10), (42, 6), (58, 6), (48, h // 2 - 10)])
        pygame.draw.polygon(ship, colors['wing'], [(18, h // 2 + 10), (42, h - 6), (58, h - 6), (48, h // 2 + 10)])
        pygame.draw.ellipse(ship, colors['glass'], (w // 2 - 18, h // 2 - 12, 28, 18))
        pygame.draw.rect(ship, colors['engine'], (0, h // 2 - 6, 14, 12), border_radius=4)
        pygame.draw.rect(ship, colors['flare'], (2, h // 2 - 3, 10, 6), border_radius=3)
        surf.blit(ship, (rect.x + 8, rect.y + 9))

    def _draw_category_icon(self, surf, category_id, rect):
        frame = pygame.Rect(rect)
        pygame.draw.rect(surf, (16, 22, 42), frame, border_radius=10)
        pygame.draw.rect(surf, (64, 105, 185), frame, 2, border_radius=10)
        cx, cy = frame.center
        col = CYAN
        if category_id == 'laser_cannon':
            pygame.draw.rect(surf, col, (cx - 18, cy - 5, 36, 10), border_radius=4)
            pygame.draw.rect(surf, WHITE, (cx + 10, cy - 2, 18, 4), border_radius=2)
        elif category_id == 'plasma_core':
            pygame.draw.circle(surf, col, (cx, cy), 16, 3)
            pygame.draw.circle(surf, WHITE, (cx, cy), 7)
        elif category_id == 'shield_generator':
            pygame.draw.polygon(surf, col, [(cx, cy - 20), (cx + 18, cy - 6), (cx + 12, cy + 18), (cx - 12, cy + 18), (cx - 18, cy - 6)], 3)
        elif category_id == 'targeting_array':
            pygame.draw.circle(surf, col, (cx, cy), 18, 3)
            pygame.draw.line(surf, WHITE, (cx - 22, cy), (cx + 22, cy), 2)
            pygame.draw.line(surf, WHITE, (cx, cy - 22), (cx, cy + 22), 2)
        elif category_id == 'thrusters':
            pygame.draw.polygon(surf, col, [(cx - 18, cy - 10), (cx + 4, cy - 10), (cx + 4, cy - 18), (cx + 22, cy), (cx + 4, cy + 18), (cx + 4, cy + 10), (cx - 18, cy + 10)], 3)
        elif category_id == 'armor_plating':
            pygame.draw.rect(surf, col, (cx - 20, cy - 16, 40, 32), 3, border_radius=6)
            pygame.draw.line(surf, WHITE, (cx - 12, cy - 8), (cx + 12, cy + 8), 2)
        elif category_id == 'missile_rack':
            pygame.draw.rect(surf, col, (cx - 20, cy - 12, 40, 24), 3, border_radius=4)
            for off in (-10, 0, 10):
                pygame.draw.circle(surf, WHITE, (cx + off, cy), 3)
        elif category_id == 'reactor':
            pygame.draw.polygon(surf, col, [(cx, cy - 18), (cx + 10, cy), (cx, cy + 18), (cx - 10, cy)], 3)
            pygame.draw.circle(surf, WHITE, (cx, cy), 5)
        elif category_id == 'cooling_system':
            for off in (-12, 0, 12):
                pygame.draw.line(surf, col, (cx + off, cy - 16), (cx + off, cy + 16), 3)
            pygame.draw.line(surf, WHITE, (cx - 18, cy), (cx + 18, cy), 2)
        elif category_id == 'wing_frame':
            pygame.draw.polygon(surf, col, [(cx - 22, cy + 8), (cx - 4, cy - 14), (cx + 4, cy - 14), (cx - 6, cy + 8)], 3)
            pygame.draw.polygon(surf, col, [(cx + 22, cy + 8), (cx + 4, cy - 14), (cx - 4, cy - 14), (cx + 6, cy + 8)], 3)
        else:
            pygame.draw.circle(surf, col, (cx, cy), 14, 3)

    def _draw_category_button(self, surf, a, button, category):
        shadow = button.rect.move(0, 4)
        pygame.draw.rect(surf, (0, 0, 0, 100), shadow, border_radius=button.radius)
        pygame.draw.rect(surf, button.color, button.rect, border_radius=button.radius)
        pygame.draw.rect(surf, (235, 240, 255), button.rect, 2, border_radius=button.radius)
        icon_rect = pygame.Rect(button.rect.x + 14, button.rect.y + 10, 56, button.rect.height - 20)
        self._draw_category_icon(surf, category['id'], icon_rect)
        label = a.render_fit(['small', 'tiny'], category['name'].upper(), WHITE, button.rect.w - 96)
        draw_text_shadow(surf, label, (icon_rect.right + 16, button.rect.centery - label.get_height() // 2), offset=(1, 1))

    def _draw_arrow_button(self, surf, button, direction):
        shadow = button.rect.move(0, 4)
        pygame.draw.rect(surf, (0, 0, 0, 100), shadow, border_radius=button.radius)
        pygame.draw.rect(surf, button.color, button.rect, border_radius=button.radius)
        pygame.draw.rect(surf, (235, 240, 255), button.rect, 2, border_radius=button.radius)
        cx, cy = button.rect.center
        if direction == 'left':
            pts = [(cx + 8, cy - 12), (cx - 8, cy), (cx + 8, cy + 12)]
        else:
            pts = [(cx - 8, cy - 12), (cx + 8, cy), (cx - 8, cy + 12)]
        pygame.draw.polygon(surf, WHITE, pts)

    def _style_action_button(self, button, owned, equipped):
        if equipped:
            button.color = (40, 180, 120)
            button.hover_color = (70, 220, 160)
            button.text_color = (240, 255, 245)
        elif owned:
            button.color = (40, 120, 255)
            button.hover_color = (75, 160, 255)
            button.text_color = WHITE
        else:
            button.color = (40, 130, 70)
            button.hover_color = (70, 170, 100)
            button.text_color = WHITE

    def _stats_text(self, stats):
        if not stats:
            return "No bonus  .  This is the stock configuration."
        parts = []
        if stats.get('damage_bonus'):
            parts.append(f"+{stats['damage_bonus']} damage")
        if stats.get('shoot_rate_delta'):
            parts.append(f"{stats['shoot_rate_delta']} fire delay")
        if stats.get('shield_bonus'):
            parts.append(f"+{stats['shield_bonus']} shield")
        if stats.get('regen_bonus'):
            parts.append(f"+{stats['regen_bonus']:.2f} shield regen")
        if stats.get('speed_bonus'):
            parts.append(f"+{stats['speed_bonus']} speed")
        if stats.get('missile'):
            parts.append("starts with missiles")
        return "  .  ".join(parts[:3])

    def _draw_stats(self, surf, a, high_score, credits):
        stats = []
        if high_score > 0:
            stats.append(f"BEST  {high_score:08d}")
        stats.append(f"CREDITS  {credits:06d}")
        text = "   ".join(stats)
        ts = a.render('small', text, YELLOW)
        pad_x, pad_y = 18, 8
        y = H - 76
        rect = pygame.Rect(W // 2 - ts.get_width() // 2 - pad_x, y - pad_y, ts.get_width() + pad_x * 2, ts.get_height() + pad_y * 2)
        back = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(back, (0, 0, 0, 150), back.get_rect(), border_radius=10)
        pygame.draw.rect(back, (*YELLOW, 95), back.get_rect(), 1, border_radius=10)
        surf.blit(back, rect.topleft)
        draw_text_shadow(surf, ts, (W // 2 - ts.get_width() // 2, y))
