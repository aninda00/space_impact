import pygame
import math
import random
import array


class AudioEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.enabled = True
        self.sfx_volume = 0.7
        self.sounds = {}
        self._init_mixer()

    def _init_mixer(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(16)
            self._generate_all_sounds()
        except Exception as e:
            print(f"[AudioEngine] Warning: Could not initialize mixer: {e}")
            self.enabled = False

    def _generate_all_sounds(self):
        sample_rate = 44100

        # 1. Laser sound (pitch drop sweep)
        self.sounds['laser'] = self._synth(
            sample_rate, 0.12,
            lambda t, dur: math.sin(2 * math.pi * (750 - 550 * (t / dur)) * t),
            lambda t, dur: math.exp(-8 * (t / dur)),
            volume=0.35
        )

        # 2. Missile / Heavy shot sound (deeper pitch drop)
        self.sounds['missile'] = self._synth(
            sample_rate, 0.22,
            lambda t, dur: math.sin(2 * math.pi * (400 - 300 * (t / dur)) * t) + 0.3 * random.uniform(-1, 1),
            lambda t, dur: math.exp(-5 * (t / dur)),
            volume=0.45
        )

        # 3. Enemy explosion (white noise + bass thwack)
        self.sounds['explosion'] = self._synth_noise(
            sample_rate, 0.25,
            decay_rate=7.0, bass_freq=90, volume=0.5
        )

        # 4. Boss explosion (long rumbling noise burst)
        self.sounds['boss_explosion'] = self._synth_noise(
            sample_rate, 0.65,
            decay_rate=3.0, bass_freq=60, volume=0.7
        )

        # 5. Shield hit / player damage (metallic ping + buzz)
        self.sounds['hit'] = self._synth(
            sample_rate, 0.15,
            lambda t, dur: math.sin(2 * math.pi * (350 + 150 * math.sin(t * 80)) * t),
            lambda t, dur: math.exp(-10 * (t / dur)),
            volume=0.5
        )

        # 6. Boss warning siren (dual tone wave pulse)
        self.sounds['boss_warn'] = self._synth(
            sample_rate, 0.45,
            lambda t, dur: math.sin(2 * math.pi * (220 if (int(t * 12) % 2 == 0) else 330) * t),
            lambda t, dur: 0.8 * (1 - t / dur),
            volume=0.55
        )

        # 7. UI Click
        self.sounds['click'] = self._synth(
            sample_rate, 0.04,
            lambda t, dur: math.sin(2 * math.pi * 1200 * t),
            lambda t, dur: math.exp(-25 * (t / dur)),
            volume=0.25
        )

        # 8. Upgrade Select (arpeggio tone)
        self.sounds['upgrade'] = self._synth(
            sample_rate, 0.25,
            lambda t, dur: math.sin(2 * math.pi * (440 * (1 + int(t * 16) % 3)) * t),
            lambda t, dur: math.exp(-4 * (t / dur)),
            volume=0.45
        )

    def _synth(self, sample_rate, duration, wave_func, env_func, volume=0.5):
        n_samples = int(sample_rate * duration)
        buf = array.array('h')
        max_amp = int(32767 * volume * self.sfx_volume)
        for i in range(n_samples):
            t = i / sample_rate
            sample_val = wave_func(t, duration) * env_func(t, duration)
            sample_val = max(-1.0, min(1.0, sample_val))
            val = int(sample_val * max_amp)
            buf.append(val)  # Left
            buf.append(val)  # Right
        try:
            return pygame.mixer.Sound(buffer=buf)
        except Exception:
            return None

    def _synth_noise(self, sample_rate, duration, decay_rate=6.0, bass_freq=80, volume=0.5):
        n_samples = int(sample_rate * duration)
        buf = array.array('h')
        max_amp = int(32767 * volume * self.sfx_volume)
        for i in range(n_samples):
            t = i / sample_rate
            noise = random.uniform(-1.0, 1.0)
            bass = math.sin(2 * math.pi * bass_freq * t)
            sample_val = (noise * 0.7 + bass * 0.3) * math.exp(-decay_rate * (t / duration))
            sample_val = max(-1.0, min(1.0, sample_val))
            val = int(sample_val * max_amp)
            buf.append(val)
            buf.append(val)
        try:
            return pygame.mixer.Sound(buffer=buf)
        except Exception:
            return None

    def play(self, sound_name):
        if not self.enabled:
            return
        snd = self.sounds.get(sound_name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass

    def set_volume(self, volume):
        self.sfx_volume = max(0.0, min(1.0, volume))
        self._generate_all_sounds()

    def toggle_mute(self):
        self.enabled = not self.enabled
        return self.enabled
