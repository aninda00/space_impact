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
            {'id': 'laser_cannon_mk3', 'name': 'Laser Cannon Mk III', 'cost': 420, 'desc': 'Military focusing coils with twin barrels.', 'stats': {'damage_bonus': 8, 'double_shot': True}},
            {'id': 'laser_cannon_mk4', 'name': 'Nova Laser Cannon', 'cost': 720, 'desc': 'Triple-beam cannon built for late-sector armor.', 'stats': {'damage_bonus': 13, 'triple_shot': True}},
        ],
    },
    {
        'id': 'plasma_core',
        'name': 'Plasma Core',
        'parts': [
            {'id': 'plasma_core_stock', 'name': 'Stock Core', 'cost': 0, 'desc': 'Stable output with no bonus.', 'stats': {}},
            {'id': 'plasma_core_overdrive', 'name': 'Overdrive Core', 'cost': 260, 'desc': 'Feeds your weapons faster between volleys.', 'stats': {'shoot_rate_delta': -2}},
            {'id': 'plasma_core_surge', 'name': 'Surge Core', 'cost': 500, 'desc': 'Pushes more charge through every firing cycle.', 'stats': {'shoot_rate_delta': -3, 'damage_bonus': 2}},
            {'id': 'plasma_core_starfire', 'name': 'Starfire Core', 'cost': 820, 'desc': 'Combat reactor tuning for constant pressure.', 'stats': {'shoot_rate_delta': -4, 'damage_bonus': 4}},
        ],
    },
    {
        'id': 'shield_generator',
        'name': 'Shield Generator',
        'parts': [
            {'id': 'shield_generator_stock', 'name': 'Stock Generator', 'cost': 0, 'desc': 'Basic defensive shell.', 'stats': {}},
            {'id': 'shield_generator_aegis', 'name': 'Aegis Generator', 'cost': 260, 'desc': 'More shield capacity for campaign bosses.', 'stats': {'shield_bonus': 35}},
            {'id': 'shield_generator_bastion', 'name': 'Bastion Generator', 'cost': 520, 'desc': 'Thicker shields with a steadier recharge curve.', 'stats': {'shield_bonus': 65, 'regen_bonus': 0.02}},
            {'id': 'shield_generator_citadel', 'name': 'Citadel Generator', 'cost': 840, 'desc': 'Heavy defensive matrix for brutal sectors.', 'stats': {'shield_bonus': 105, 'regen_bonus': 0.04}},
        ],
    },
    {
        'id': 'targeting_array',
        'name': 'Targeting Array',
        'parts': [
            {'id': 'targeting_array_stock', 'name': 'Stock Array', 'cost': 0, 'desc': 'Manual lock and standard tracking.', 'stats': {}},
            {'id': 'targeting_array_hawk', 'name': 'Hawk Array', 'cost': 210, 'desc': 'Improves shot focus and impact.', 'stats': {'damage_bonus': 3}},
            {'id': 'targeting_array_viper', 'name': 'Viper Array', 'cost': 430, 'desc': 'Predictive targeting for faster wave clears.', 'stats': {'damage_bonus': 5, 'shoot_rate_delta': -1}},
            {'id': 'targeting_array_oracle', 'name': 'Oracle Array', 'cost': 760, 'desc': 'Elite fire-control package for boss armor.', 'stats': {'damage_bonus': 8, 'shoot_rate_delta': -2, 'piercing': True}},
        ],
    },
    {
        'id': 'thrusters',
        'name': 'Thrusters',
        'parts': [
            {'id': 'thrusters_stock', 'name': 'Stock Thrusters', 'cost': 0, 'desc': 'Standard movement package.', 'stats': {}},
            {'id': 'thrusters_vector', 'name': 'Vector Thrusters', 'cost': 230, 'desc': 'Adds more speed for dodging lanes.', 'stats': {'speed_bonus': 5}},
            {'id': 'thrusters_comet', 'name': 'Comet Thrusters', 'cost': 440, 'desc': 'Stronger vertical response under pressure.', 'stats': {'speed_bonus': 8, 'regen_bonus': 0.01}},
            {'id': 'thrusters_flux', 'name': 'Flux Thrusters', 'cost': 720, 'desc': 'Fast recovery package for dense bullet patterns.', 'stats': {'speed_bonus': 12, 'regen_bonus': 0.02}},
        ],
    },
    {
        'id': 'armor_plating',
        'name': 'Armor Plating',
        'parts': [
            {'id': 'armor_plating_stock', 'name': 'Stock Plating', 'cost': 0, 'desc': 'No extra reinforcement.', 'stats': {}},
            {'id': 'armor_plating_titan', 'name': 'Titan Plating', 'cost': 300, 'desc': 'Thickens the frame and boosts shield reserve.', 'stats': {'shield_bonus': 25, 'regen_bonus': 0.01}},
            {'id': 'armor_plating_guardian', 'name': 'Guardian Plating', 'cost': 560, 'desc': 'Layered armor that keeps shields stable.', 'stats': {'shield_bonus': 55, 'regen_bonus': 0.025}},
            {'id': 'armor_plating_colossus', 'name': 'Colossus Plating', 'cost': 880, 'desc': 'Late-sector armor built to absorb mistakes.', 'stats': {'shield_bonus': 90, 'regen_bonus': 0.04}},
        ],
    },
    {
        'id': 'missile_rack',
        'name': 'Missile Rack',
        'parts': [
            {'id': 'missile_rack_stock', 'name': 'Empty Rack', 'cost': 0, 'desc': 'No support ordnance.', 'stats': {}},
            {'id': 'missile_rack_seeker', 'name': 'Seeker Rack', 'cost': 420, 'desc': 'Campaign runs start with homing missiles online.', 'stats': {'missile': True, 'missile_interval': 4}},
            {'id': 'missile_rack_hunter', 'name': 'Hunter Rack', 'cost': 700, 'desc': 'More frequent missile support against elites.', 'stats': {'missile': True, 'missile_interval': 3, 'damage_bonus': 2}},
            {'id': 'missile_rack_tempest', 'name': 'Tempest Rack', 'cost': 980, 'desc': 'Aggressive missile cadence for boss phases.', 'stats': {'missile': True, 'missile_interval': 2, 'damage_bonus': 3}},
        ],
    },
    {
        'id': 'reactor',
        'name': 'Reactor',
        'parts': [
            {'id': 'reactor_stock', 'name': 'Stock Reactor', 'cost': 0, 'desc': 'Safe civilian output levels.', 'stats': {}},
            {'id': 'reactor_stellar', 'name': 'Stellar Reactor', 'cost': 340, 'desc': 'Feeds both shields and weapon systems.', 'stats': {'damage_bonus': 2, 'shield_bonus': 20}},
            {'id': 'reactor_pulsar', 'name': 'Pulsar Reactor', 'cost': 620, 'desc': 'Balanced combat output for mid campaign.', 'stats': {'damage_bonus': 4, 'shield_bonus': 35, 'regen_bonus': 0.01}},
            {'id': 'reactor_quasar', 'name': 'Quasar Reactor', 'cost': 940, 'desc': 'Premium power plant for the final sectors.', 'stats': {'damage_bonus': 6, 'shield_bonus': 55, 'regen_bonus': 0.02}},
        ],
    },
    {
        'id': 'cooling_system',
        'name': 'Cooling System',
        'parts': [
            {'id': 'cooling_system_stock', 'name': 'Stock Cooling', 'cost': 0, 'desc': 'Keeps the ship just stable enough.', 'stats': {}},
            {'id': 'cooling_system_cryo', 'name': 'Cryo Cooling', 'cost': 240, 'desc': 'Lets the guns cycle harder for longer.', 'stats': {'shoot_rate_delta': -1, 'regen_bonus': 0.02}},
            {'id': 'cooling_system_frostline', 'name': 'Frostline Cooling', 'cost': 460, 'desc': 'Improves heat control for sustained fire.', 'stats': {'shoot_rate_delta': -2, 'regen_bonus': 0.03}},
            {'id': 'cooling_system_zero', 'name': 'Zero-Point Cooling', 'cost': 780, 'desc': 'Keeps elite weapon systems from choking.', 'stats': {'shoot_rate_delta': -3, 'regen_bonus': 0.05}},
        ],
    },
    {
        'id': 'wing_frame',
        'name': 'Wing Frame',
        'parts': [
            {'id': 'wing_frame_stock', 'name': 'Stock Frame', 'cost': 0, 'desc': 'No structural tuning.', 'stats': {}},
            {'id': 'wing_frame_raptor', 'name': 'Raptor Frame', 'cost': 280, 'desc': 'Lightens the hull and helps your turns recover.', 'stats': {'speed_bonus': 3, 'damage_bonus': 2}},
            {'id': 'wing_frame_striker', 'name': 'Striker Frame', 'cost': 520, 'desc': 'A responsive frame with better weapon mounts.', 'stats': {'speed_bonus': 6, 'damage_bonus': 4}},
            {'id': 'wing_frame_valkyrie', 'name': 'Valkyrie Frame', 'cost': 860, 'desc': 'Precision frame for surviving late-sector lanes.', 'stats': {'speed_bonus': 9, 'damage_bonus': 6}},
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


def part_power(part_id):
    part = PARTS_BY_ID.get(part_id)
    if not part:
        return 0
    stats = part['stats']
    power = 0
    power += stats.get('damage_bonus', 0) * 18
    power += abs(stats.get('shoot_rate_delta', 0)) * 26
    power += stats.get('shield_bonus', 0) * 1.2
    power += stats.get('regen_bonus', 0) * 900
    power += stats.get('speed_bonus', 0) * 9
    if stats.get('missile'):
        interval = max(1, stats.get('missile_interval', 5))
        power += 120 + (5 - min(interval, 5)) * 35
    if stats.get('double_shot'):
        power += 180
    if stats.get('triple_shot'):
        power += 320
    if stats.get('piercing'):
        power += 180
    return int(power)


def campaign_power(equipped_parts):
    if isinstance(equipped_parts, dict):
        part_ids = equipped_parts.values()
    else:
        part_ids = equipped_parts or []
    return sum(part_power(part_id) for part_id in part_ids)


def recommended_power(sector):
    sector = max(1, int(sector or 1))
    return max(0, (sector - 1) * 145)
