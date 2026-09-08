import pygame
pygame.init()
from ui.menu import MainMenu
from core.settings import W, H
from systems.loadout import PART_CATEGORIES, SKINS

screen = pygame.display.set_mode((W, H))
menu = MainMenu()
menu._screen = 'shop'

# Test all skins
print("Testing skin previews...")
for skin_idx, skin in enumerate(SKINS):
    menu._skin_index = skin_idx
    menu.draw(screen, 0, 10000)
    print(f'Skin: {skin["id"]} ({skin["name"]}) - OK')

# Test all categories and parts
print("\nTesting part previews...")
for cat_idx, cat in enumerate(PART_CATEGORIES):
    menu._selected_category_index = cat_idx
    parts = cat['parts']
    for part_idx, part in enumerate(parts):
        menu._selected_part_indices[cat['id']] = part_idx
        menu.draw(screen, 0, 10000)
        icon = cat.get('icon_type', 'none')
        tier = part.get('icon_tier', 0)
        print(f'Category: {cat["id"]}, Part: {part["id"]}, Icon: {icon}, Tier: {tier} - OK')

print('\nAll skins, categories and parts tested successfully!')