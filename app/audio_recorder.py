import numpy as np
from app.config import CHUNK_SIZE, SAMPLE_RATE, VAD_THRESHOLD, VAD_SILENCE_DURATION
from faster_whisper.vad import get_speech_timestamps
from colorama import Fore, Style

class AudioRecorder:
    def __init__(self):
        self.frames = []
        self.is_recording = False
        self.silence_counter = 0.0
        self.speech_started = False
    
    def start_recording(self):
        # Czyści stare dane i przygotowuje system do zapisu
        self.is_recording = True
        self.frames.clear()
        self.silence_counter = 0.0
        self.speech_started = False

    def record_chunk(self, stream):
        # Pobiera pojedynczą paczkę danych audio z karty dźwiękowej i odkłada do RAM
        audio_chunk, error_flag = stream.read(CHUNK_SIZE)
        self.frames.append(audio_chunk)

        flat_audio = audio_chunk.flatten()

        timestamps = get_speech_timestamps(
            flat_audio,
            sampling_rate=SAMPLE_RATE,
            threshold = VAD_THRESHOLD,
            min_silence_duration_ms=200
        )

        if len(timestamps) > 0:
            if not self.speech_started:
                print(f"\n{Fore.CYAN}[SYSTEM]: Wykryłem głos, nagrywam...{Style.RESET_ALL}")
            self.speech_started = True
            self.silence_counter = 0.0
        else:
            # Jeśli funkcja zwróciła pustą listę – mamy ciszę
            chunk_duration = CHUNK_SIZE / SAMPLE_RATE
            self.silence_counter += chunk_duration

            if self.silence_counter >= VAD_SILENCE_DURATION:
                print(f"{Fore.CYAN}[SYSTEM]: Wykryto koniec wypowiedzi (cisza).{Style.RESET_ALL}")
                self.is_recording = False

    def stop_recording(self):
        self.is_recording = False
        if not self.frames:
            return np.zeros(0, dtype=np.float32)
        merged_data = np.concatenate(self.frames, axis=0).flatten()
        return merged_data