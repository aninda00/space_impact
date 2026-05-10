SKINS = [
    {
        'id': 'classic',
        'name': 'Classic Blue',
        'cost': 0,
        'desc': 'The stock fleet finish.',
        'colors': {
            'body': (55, 155, 255),
            'nose': (40, 215, 240),
            'wing': (55, 155, 255),
            'glass': (80, 170, 255, 180),
            'engine': (255, 130, 40),
            'flare': (255, 200, 40),
        },
    },
    {
        'id': 'ember',
        'name': 'Ember Strike',
        'cost': 180,
        'desc': 'Burnt alloy with a hot engine bloom.',
        'colors': {
            'body': (210, 70, 55),
            'nose': (255, 170, 60),
            'wing': (185, 55, 48),
            'glass': (255, 225, 170, 180),
            'engine': (255, 210, 70),
            'flare': (255, 245, 140),
        },
    },
    {
        'id': 'aurora',
        'name': 'Aurora Lance',
        'cost': 320,
        'desc': 'Cool neon plating and a bright canopy.',
        'colors': {
            'body': (60, 210, 170),
            'nose': (175, 255, 240),
            'wing': (40, 170, 145),
            'glass': (200, 255, 255, 190),
            'engine': (80, 255, 215),
            'flare': (220, 255, 245),
        },
    },
    {
        'id': 'phantom',
        'name': 'Phantom Alloy',
        'cost': 520,
        'desc': 'Dark hull with stealth violet highlights.',
        'colors': {
            'body': (95, 95, 135),
            'nose': (190, 120, 255),
            'wing': (78, 78, 118),
            'glass': (210, 180, 255, 180),
            'engine': (220, 120, 255),
            'flare': (255, 180, 255),
        },
    },
]

PART_CATEGORIES = [
    {
        'id': 'laser_cannon',
        'name': 'Laser Cannon',
        'parts': [
            {'id': 'laser_cannon_stock', 'name': 'Stock Laser', 'cost': 0, 'desc': 'Standard issue forward cannon.', 'stats': {}},
            {'id': 'laser_cannon_mk2', 'name': 'Laser Cannon Mk II', 'cost': 220, 'desc': 'Sharper beams and tighter damage falloff.', 'stats': {'damage_bonus': 4}},
        ],
    },
    {
        'id': 'plasma_core',
        'name': 'Plasma Core',
        'parts': [
            {'id': 'plasma_core_stock', 'name': 'Stock Core', 'cost': 0, 'desc': 'Stable output with no bonus.', 'stats': {}},
            {'id': 'plasma_core_overdrive', 'name': 'Overdrive Core', 'cost': 260, 'desc': 'Feeds your weapons faster between volleys.', 'stats': {'shoot_rate_delta': -2}},
        ],
    },
    {
        'id': 'shield_generator',
        'name': 'Shield Generator',
        'parts': [
            {'id': 'shield_generator_stock', 'name': 'Stock Generator', 'cost': 0, 'desc': 'Basic defensive shell.', 'stats': {}},
            {'id': 'shield_generator_aegis', 'name': 'Aegis Generator', 'cost': 260, 'desc': 'More shield capacity for campaign bosses.', 'stats': {'shield_bonus': 35}},
        ],
    },
    {
        'id': 'targeting_array',
        'name': 'Targeting Array',
        'parts': [
            {'id': 'targeting_array_stock', 'name': 'Stock Array', 'cost': 0, 'desc': 'Manual lock and standard tracking.', 'stats': {}},
            {'id': 'targeting_array_hawk', 'name': 'Hawk Array', 'cost': 210, 'desc': 'Improves shot focus and impact.', 'stats': {'damage_bonus': 3}},
        ],
    },
    {
        'id': 'thrusters',
        'name': 'Thrusters',
        'parts': [
            {'id': 'thrusters_stock', 'name': 'Stock Thrusters', 'cost': 0, 'desc': 'Standard movement package.', 'stats': {}},
            {'id': 'thrusters_vector', 'name': 'Vector Thrusters', 'cost': 230, 'desc': 'Adds more speed for dodging lanes.', 'stats': {'speed_bonus': 5}},
        ],
    },
    {
        'id': 'armor_plating',
        'name': 'Armor Plating',
        'parts': [
            {'id': 'armor_plating_stock', 'name': 'Stock Plating', 'cost': 0, 'desc': 'No extra reinforcement.', 'stats': {}},
            {'id': 'armor_plating_titan', 'name': 'Titan Plating', 'cost': 300, 'desc': 'Thickens the frame and boosts shield reserve.', 'stats': {'shield_bonus': 25, 'regen_bonus': 0.01}},
        ],
    },
    {
        'id': 'missile_rack',
        'name': 'Missile Rack',
        'parts': [
            {'id': 'missile_rack_stock', 'name': 'Empty Rack', 'cost': 0, 'desc': 'No support ordnance.', 'stats': {}},
            {'id': 'missile_rack_seeker', 'name': 'Seeker Rack', 'cost': 420, 'desc': 'Campaign runs start with homing missiles online.', 'stats': {'missile': True, 'missile_interval': 4}},
        ],
    },
    {
        'id': 'reactor',
        'name': 'Reactor',
        'parts': [
            {'id': 'reactor_stock', 'name': 'Stock Reactor', 'cost': 0, 'desc': 'Safe civilian output levels.', 'stats': {}},
            {'id': 'reactor_stellar', 'name': 'Stellar Reactor', 'cost': 340, 'desc': 'Feeds both shields and weapon systems.', 'stats': {'damage_bonus': 2, 'shield_bonus': 20}},
        ],
    },
    {
        'id': 'cooling_system',
        'name': 'Cooling System',
        'parts': [
            {'id': 'cooling_system_stock', 'name': 'Stock Cooling', 'cost': 0, 'desc': 'Keeps the ship just stable enough.', 'stats': {}},
            {'id': 'cooling_system_cryo', 'name': 'Cryo Cooling', 'cost': 240, 'desc': 'Lets the guns cycle harder for longer.', 'stats': {'shoot_rate_delta': -1, 'regen_bonus': 0.02}},
        ],
    },
    {
        'id': 'wing_frame',
        'name': 'Wing Frame',
        'parts': [
            {'id': 'wing_frame_stock', 'name': 'Stock Frame', 'cost': 0, 'desc': 'No structural tuning.', 'stats': {}},
            {'id': 'wing_frame_raptor', 'name': 'Raptor Frame', 'cost': 280, 'desc': 'Lightens the hull and helps your turns recover.', 'stats': {'speed_bonus': 3, 'damage_bonus': 2}},
        ],
    },
]

SKINS_BY_ID = {item['id']: item for item in SKINS}
PARTS_BY_ID = {}
PART_CATEGORY_BY_ID = {}
DEFAULT_EQUIPPED_PARTS = {}

for category in PART_CATEGORIES:
    PART_CATEGORY_BY_ID[category['id']] = category
    DEFAULT_EQUIPPED_PARTS[category['id']] = category['parts'][0]['id']
    for part in category['parts']:
        part = dict(part)
        part['category_id'] = category['id']
        PARTS_BY_ID[part['id']] = part
