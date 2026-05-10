# Space Impact — Remastered

A full-featured Space Impact clone built with Python + pygame.

## Setup

```bash
pip install pygame
python main.py
```

## Controls

| Action | Control |
|--------|---------|
| Move up / down | Mouse scroll wheel |
| Shoot | Automatic |
| Pause / Resume | ESC |
| Save progress | F5 (during gameplay) |
| Quit from menu | ESC |

## Game Structure

```
space_impact/
├── main.py                   # Entry point
├── core/
│   ├── settings.py           # All constants & config
│   ├── assets.py             # Font/asset loader (singleton)
│   └── game.py               # State machine & main loop
├── entities/
│   ├── player.py             # Player ship
│   ├── enemy.py              # Data-driven enemy definitions and factory
│   ├── boss.py               # Data-driven boss definitions and factory
│   ├── bullet.py             # Player bullets, missiles, enemy bullets
│   └── effects.py            # Explosions, particles, starfield
├── systems/
│   ├── wave_manager.py       # Wave spawning & progression
│   ├── upgrade_system.py     # Upgrade tree & application
│   └── story.py              # Story text per sector
└── ui/
    ├── hud.py                # In-game HUD
    ├── menu.py               # Main menu
    ├── upgrade_screen.py     # Between-wave upgrade picker
    └── components.py         # Button, ProgressBar, Panel
```

## Features

- **13 Sectors** with unique story briefings
- **8 Enemy Types**: Scout, Fighter, Bomber, Elite, Interceptor, Bulwark, Wraith, Dreadnought
- **13 Bosses**: Each with unique attack patterns and phases
- **Data-driven rosters**: Add ships in `ENEMY_DEFS` and bosses in `BOSS_DEFS`
- **10 Upgrades**: Rapid Fire, Twin Cannons, Triple Spread, Phase Rounds,
  Armor Piercer, Shield Matrix, Nano Repair, Reserve Pilot, Homing Missile, Afterburner
- **Lives + Shield system**: Lose shield → lose a life, shield regenerates
- **High score** saved locally (save.json)
- **Modern HUD**: Score, shield bar, wave progress, kill floaters
