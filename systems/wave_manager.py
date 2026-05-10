from core.settings import FPS, WAVES_PER_SECTOR, TOTAL_SECTORS
from entities.enemy import choose_enemy_id, create_enemy
from entities.boss import SECTOR_BOSSES


class WaveManager:
    def __init__(self, mode='campaign'):
        self.mode        = mode
        self.sector      = 1
        self.wave        = 0
        self.wave_kills  = 0
        self.wave_goal   = 0
        self.spawn_timer = 0
        self.spawn_rate  = 90
        self.speed_mult  = 1.0
        self.boss_active = False
        self.boss        = None
        self.spawning    = True   # stops when kill goal reached
        self.state       = 'idle'
        self.mode_timer  = 0
        self.next_upgrade_timer = 0
        self.time_limit  = FPS * 300
        self.time_left   = self.time_limit

    def set_mode(self, mode):
        self.mode = mode

    def start_sector(self, sector):
        self.sector      = sector
        self.wave        = 0
        self.boss_active = False
        self.boss        = None
        self.speed_mult  = 1.0 + (sector - 1) * 0.24
        self.start_next_wave()

    def start_boss_rush(self):
        self.sector      = 1
        self.wave        = 1
        self.wave_kills  = 0
        self.wave_goal   = TOTAL_SECTORS
        self.boss_active = False
        self.boss        = None
        self.speed_mult  = 1.0
        self.state       = 'boss_warning'

    def start_survival(self):
        self.sector      = 1
        self.wave        = 1
        self.wave_kills  = 0
        self.wave_goal   = FPS * 90
        self.spawn_timer = 0
        self.mode_timer  = 0
        self.next_upgrade_timer = FPS * 90
        self.spawning    = True
        self.state       = 'survival'
        self._set_pressure(1)

    def start_time_attack(self):
        self.sector      = 1
        self.wave        = 1
        self.wave_kills  = 0
        self.wave_goal   = self.time_limit
        self.spawn_timer = 0
        self.mode_timer  = 0
        self.time_left   = self.time_limit
        self.next_upgrade_timer = FPS * 60
        self.spawning    = True
        self.state       = 'time_attack'
        self._set_pressure(1)

    def resume_special_mode(self):
        if self.mode == 'survival':
            self.state = 'survival'
            self.next_upgrade_timer = FPS * 90
            self.spawning = True
        elif self.mode == 'time_attack':
            self.state = 'time_attack'
            self.next_upgrade_timer = FPS * 60
            self.spawning = True

    def prepare_next_boss(self):
        self.boss_active = False
        self.boss = None
        self.state = 'boss_warning'

    def start_next_wave(self):
        self.wave       += 1
        self.wave_kills  = 0
        self.wave_goal   = self._calc_goal()
        self.spawn_timer = 0
        if self.mode == 'endless':
            tier = self._enemy_sector()
            self.speed_mult = 1.0 + (tier - 1) * 0.18 + (self.wave - 1) * 0.025
            self.spawn_rate = max(18, 92 - tier * 7 - self.wave * 3)
        else:
            self.speed_mult = 1.0 + (self.sector - 1) * 0.24
            self.spawn_rate = max(20, 92 - self.sector * 8 - self.wave * 5)
        self.spawning    = True
        self.state       = 'wave'

    def update(self, enemies_group, e_bullets_group, delta_kills=0):
        self.wave_kills += delta_kills

        if self.mode == 'survival':
            return self._update_survival(enemies_group)

        if self.mode == 'time_attack':
            return self._update_time_attack(enemies_group)

        if self.state == 'wave':
            # Stop spawning once kill goal is reached
            if self.wave_kills >= self.wave_goal:
                self.spawning = False

            if self.spawning:
                self.spawn_timer += 1
                if self.spawn_timer >= self.spawn_rate:
                    self.spawn_timer = 0
                    self._spawn(enemies_group)

            # Wave clear: goal reached AND all remaining enemies dead
            if not self.spawning and len(enemies_group) == 0:
                if self.mode == 'endless':
                    if self.wave % 3 == 0:
                        self.state = 'wave_clear'
                        return 'upgrade'
                    self.start_next_wave()
                    return 'next_wave'
                elif self.wave >= WAVES_PER_SECTOR:
                    self.state = 'boss_warning'
                    return 'boss_warning'
                else:
                    self.state = 'wave_clear'
                    return 'upgrade'

        elif self.state == 'boss':
            if self.boss:
                bullets = self.boss.update()
                for b in bullets:
                    e_bullets_group.add(b)
                if self.boss.hp <= 0:
                    self.boss.kill()
                    self.boss        = None
                    self.boss_active = False
                    if self.mode == 'boss_rush':
                        if self.sector >= TOTAL_SECTORS:
                            self.state = 'game_clear'
                            return 'game_clear'
                        self.sector += 1
                        self.wave = self.sector
                        self.state = 'boss_clear'
                        return 'upgrade'
                    if self.sector >= TOTAL_SECTORS:
                        self.state = 'game_clear'
                        return 'game_clear'
                    else:
                        self.state = 'sector_clear'
                        return 'sector_clear'

        return None

    def spawn_boss(self, enemies_group, sprites_all):
        if self.mode == 'endless':
            return
        BossClass        = SECTOR_BOSSES[self.sector - 1]
        self.boss        = BossClass()
        sprites_all.add(self.boss)
        self.boss_active = True
        self.state       = 'boss'

    def add_time_bonus(self, frames):
        if self.mode != 'time_attack':
            return
        self.time_left = min(self.time_limit + FPS * 30, self.time_left + frames)

    def _update_survival(self, enemies_group):
        if self.state != 'survival':
            return None
        self.mode_timer += 1
        self.next_upgrade_timer -= 1
        self.wave = 1 + self.mode_timer // (FPS * 45)
        self._set_pressure(self._survival_tier())
        self._spawn_continuous(enemies_group)
        if self.next_upgrade_timer <= 0:
            self.state = 'survival_break'
            return 'upgrade'
        return None

    def _update_time_attack(self, enemies_group):
        if self.state != 'time_attack':
            return None
        self.mode_timer += 1
        self.time_left -= 1
        self.next_upgrade_timer -= 1
        self.wave = 1 + self.mode_timer // (FPS * 30)
        self._set_pressure(self._time_attack_tier())
        self._spawn_continuous(enemies_group)
        if self.time_left <= 0:
            self.state = 'game_clear'
            return 'game_clear'
        if self.next_upgrade_timer <= 0:
            self.state = 'time_break'
            return 'upgrade'
        return None

    def _spawn_continuous(self, enemies_group):
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_rate:
            self.spawn_timer = 0
            self._spawn(enemies_group)

    def _set_pressure(self, tier):
        self.speed_mult = 1.0 + (tier - 1) * 0.16 + max(0, self.wave - 1) * 0.02
        self.spawn_rate = max(16, 86 - tier * 6 - self.wave * 2)

    def _calc_goal(self):
        if self.mode == 'endless':
            tier = self._endless_tier()
            return 12 + self.wave * 3 + tier * 3
        return 10 + self.wave * 3 + self.sector * 4

    def _spawn(self, enemies_group):
        enemy_id = choose_enemy_id(self._enemy_sector())
        enemies_group.add(create_enemy(enemy_id, speed_mult=self.speed_mult))

    def _endless_tier(self):
        return min(TOTAL_SECTORS, 1 + max(0, self.wave - 1) // 3)

    def _survival_tier(self):
        return min(TOTAL_SECTORS, 1 + max(0, self.mode_timer) // (FPS * 90))

    def _time_attack_tier(self):
        return min(TOTAL_SECTORS, 1 + max(0, self.mode_timer) // (FPS * 60))

    def _enemy_sector(self):
        if self.mode == 'endless':
            return self._endless_tier()
        if self.mode == 'survival':
            return self._survival_tier()
        if self.mode == 'time_attack':
            return self._time_attack_tier()
        return self.sector

    def wave_progress(self):
        if self.mode == 'boss_rush':
            return min(1.0, self.sector / TOTAL_SECTORS)
        if self.mode == 'survival':
            return 1.0 - max(0, self.next_upgrade_timer) / max(1, FPS * 90)
        if self.mode == 'time_attack':
            return max(0.0, self.time_left / self.time_limit)
        if self.wave_goal == 0:
            return 0
        return min(1.0, self.wave_kills / self.wave_goal)

    def display_wave(self):    return self.wave
    def display_sector(self):
        if self.mode == 'endless':
            return self._endless_tier()
        if self.mode == 'survival':
            return self._survival_tier()
        if self.mode == 'time_attack':
            return self._time_attack_tier()
        return self.sector

    def display_time(self):
        frames = self.time_left if self.mode == 'time_attack' else self.mode_timer
        seconds = max(0, frames // FPS)
        return f"{seconds // 60}:{seconds % 60:02d}"
