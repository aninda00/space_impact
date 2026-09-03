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
        self.music_volume = 0.5
        self.sounds = {}
        self.music_sounds = {}
        self.music_channel = None
        self.current_track = None
        self._init_mixer()

    def _init_mixer(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(16)
            self.music_channel = pygame.mixer.Channel(0)
            self._generate_all_sounds()
            self._generate_all_music()
            self.update_music_volume()
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

    def _generate_all_music(self):
        sample_rate = 44100
        # 1. Menu Track — Ambient Am-F-C-G space chord loop
        self.music_sounds['menu_music'] = self._synth_music(
            sample_rate, duration=4.0,
            bass_freqs=[110, 87, 130, 98],
            arp_notes=[220, 261, 329, 392, 440, 523, 659, 784],
            bpm=90, style='ambient'
        )
        # 2. Gameplay Track — Driving 120 BPM synthwave battle arpeggios
        self.music_sounds['gameplay_music'] = self._synth_music(
            sample_rate, duration=4.0,
            bass_freqs=[110, 110, 130, 98],
            arp_notes=[220, 277, 329, 440, 554, 659, 880, 659],
            bpm=120, style='battle'
        )
        # 3. Boss Track — Fast 140 BPM tense dual-tone surge
        self.music_sounds['boss_music'] = self._synth_music(
            sample_rate, duration=3.4,
            bass_freqs=[73, 77, 73, 82],
            arp_notes=[146, 155, 293, 311, 587, 622, 1174, 1244],
            bpm=140, style='boss'
        )
        # 4. Victory Track — Major triad fanfare
        self.music_sounds['victory_music'] = self._synth_music(
            sample_rate, duration=3.0,
            bass_freqs=[130, 164, 196, 261],
            arp_notes=[261, 329, 392, 523, 659, 784, 1046, 1318],
            bpm=110, style='victory'
        )

    def _synth_music(self, sample_rate, duration, bass_freqs, arp_notes, bpm=120, style='ambient'):
        n_samples = int(sample_rate * duration)
        buf = array.array('h')
        max_amp = 32767 * 0.35
        beats_per_sec = bpm / 60.0

        for i in range(n_samples):
            t = i / sample_rate
            beat = t * beats_per_sec
            measure = int(beat // 4) % len(bass_freqs)
            step = int(beat * 4) % len(arp_notes)

            # Sub bass synth line
            bass_f = bass_freqs[measure]
            bass_wave = math.sin(2 * math.pi * bass_f * t)

            # Arpeggio lead synth line
            arp_f = arp_notes[step]
            step_phase = (beat * 4) % 1.0
            env = math.exp(-4.0 * step_phase)
            if style == 'boss':
                # Square wave for aggressive synth lead
                arp_wave = (1.0 if math.sin(2 * math.pi * arp_f * t) > 0 else -1.0) * env
            else:
                arp_wave = math.sin(2 * math.pi * arp_f * t) * env

            # Percussion pulse on quarter beats
            beat_phase = beat % 1.0
            percussion = random.uniform(-0.15, 0.15) * math.exp(-12.0 * beat_phase)

            sample_val = bass_wave * 0.4 + arp_wave * 0.45 + percussion * 0.15
            sample_val = max(-1.0, min(1.0, sample_val))
            val = int(sample_val * max_amp)
            buf.append(val)
            buf.append(val)
        try:
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

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
            return pygame.mixer.Sound(buffer=bytes(buf))
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
            return pygame.mixer.Sound(buffer=bytes(buf))
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

    def play_music(self, track_name):
        if not self.music_channel:
            return
        if self.current_track == track_name and self.music_channel.get_busy():
            return
        snd = self.music_sounds.get(track_name)
        if snd:
            try:
                self.current_track = track_name
                self.music_channel.play(snd, loops=-1)
                self.update_music_volume()
            except Exception:
                pass

    def stop_music(self):
        if self.music_channel:
            self.music_channel.stop()
            self.current_track = None

    def update_music_volume(self):
        if self.music_channel:
            effective_vol = self.music_volume if self.enabled else 0.0
            self.music_channel.set_volume(effective_vol)

    def set_sfx_volume(self, volume):
        self.sfx_volume = max(0.0, min(1.0, float(volume)))
        self._generate_all_sounds()

    def set_music_volume(self, volume):
        self.music_volume = max(0.0, min(1.0, float(volume)))
        self.update_music_volume()

    def set_muted(self, muted):
        self.enabled = not bool(muted)
        self.update_music_volume()

    def set_volume(self, volume):
        self.set_sfx_volume(volume)

    def toggle_mute(self):
        self.enabled = not self.enabled
        self.update_music_volume()
        return self.enabled
