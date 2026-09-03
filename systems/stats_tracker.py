"""
systems/stats_tracker.py
------------------------
Tracks per-run gameplay statistics for Space Impact — Remastered.
Records accuracy, damage dealt/taken, boss kills, and run duration,
then exposes a summary dict for the end-of-run screens.
"""
import time


class StatsTracker:
    """
    Lightweight, zero-dependency run statistics tracker.
    Create one at the start of each run and query at the end.
    """

    def __init__(self):
        self.reset()

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def reset(self):
        """Reset all counters — call when a new run begins."""
        self._start_time   = time.monotonic()
        self.shots_fired   = 0
        self.shots_hit     = 0
        self.damage_dealt  = 0
        self.damage_taken  = 0
        self.enemies_killed = 0
        self.bosses_killed = 0
        self.missiles_fired = 0
        self.missiles_hit   = 0

    # ── Recording API ─────────────────────────────────────────────────────

    def record_shot(self, is_missile=False):
        if is_missile:
            self.missiles_fired += 1
        else:
            self.shots_fired += 1

    def record_hit(self, damage, is_missile=False):
        """Call when a player bullet/missile strikes an enemy."""
        if is_missile:
            self.missiles_hit += 1
        else:
            self.shots_hit += 1
        self.damage_dealt += int(damage)

    def record_damage_taken(self, damage):
        self.damage_taken += int(damage)

    def record_enemy_killed(self):
        self.enemies_killed += 1

    def record_boss_killed(self):
        self.bosses_killed += 1
        self.enemies_killed += 1

    # ── Derived Metrics ───────────────────────────────────────────────────

    @property
    def run_duration_seconds(self):
        return time.monotonic() - self._start_time

    @property
    def accuracy(self):
        """Bullet accuracy as a 0–100 float. Missiles excluded."""
        if self.shots_fired == 0:
            return 0.0
        return min(100.0, 100.0 * self.shots_hit / self.shots_fired)

    @property
    def missile_accuracy(self):
        if self.missiles_fired == 0:
            return None  # N/A — no missiles used
        return min(100.0, 100.0 * self.missiles_hit / self.missiles_fired)

    @property
    def run_duration_str(self):
        total = int(self.run_duration_seconds)
        m, s  = divmod(total, 60)
        h, m  = divmod(m, 60)
        if h:
            return f"{h}h {m:02d}m {s:02d}s"
        return f"{m:02d}m {s:02d}s"

    # ── Summary ───────────────────────────────────────────────────────────

    def summary(self):
        """Return a list of (label, value_str) tuples for display."""
        rows = [
            ("RUN TIME",       self.run_duration_str),
            ("ENEMIES KILLED", str(self.enemies_killed)),
            ("BOSSES KILLED",  str(self.bosses_killed)),
            ("SHOTS FIRED",    str(self.shots_fired)),
            ("ACCURACY",       f"{self.accuracy:.1f}%"),
            ("DAMAGE DEALT",   f"{self.damage_dealt:,}"),
            ("DAMAGE TAKEN",   f"{self.damage_taken:,}"),
        ]
        ma = self.missile_accuracy
        if ma is not None:
            rows.append(("MISSILE ACC.", f"{ma:.1f}%"))
        return rows
