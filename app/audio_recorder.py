"""
Moduł odpowiedzialny za nagrywanie mowy użytkownika z mikrofonu wraz
z automatycznym wykrywaniem aktywności głosowej (VAD - Voice Activity Detection).

Nagrywanie kończy się automatycznie, gdy po wykryciu mowy nastąpi cisza
trwająca dłużej niż VAD_SILENCE_DURATION sekund - dzięki temu użytkownik
nie musi ręcznie sygnalizować końca wypowiedzi.
"""
import numpy as np
from app.config import CHUNK_SIZE, SAMPLE_RATE, VAD_THRESHOLD, VAD_SILENCE_DURATION, SILENCE_TIMER
from faster_whisper.vad import get_speech_timestamps
from app.logger import get_logger

logger = get_logger(__name__)

class AudioRecorder:
    """Rejestruje audio z mikrofonu paczka po paczce i wykrywa moment
    zakończenia wypowiedzi na podstawie ciszy (VAD).

    Atrybuty:
        frames: lista zebranych dotąd paczek audio (numpy arrays).
        is_recording: flaga informująca, czy nagrywanie jest aktywne.
        silence_counter: skumulowany czas (w sekundach) ciszy od ostatnio wykrytej mowy.
        speech_started: czy w bieżącym nagraniu wykryto już jakikolwiek fragment mowy.
    """
    def __init__(self):
        self.frames = []
        self.is_recording = False
        self.silence_counter = 0.0
        self.speech_started = False
    
    def start_recording(self):
        """Resetuje stan rejestratora i rozpoczyna nową sesję nagrywania."""
        # Czyści stare dane i przygotowuje system do zapisu
        self.is_recording = True
        self.frames.clear()
        self.silence_counter = 0.0
        self.speech_started = False

    def record_chunk(self, stream):
        """Odczytuje jedną paczkę audio ze strumienia mikrofonu, zapisuje ją
        w buforze `frames` i sprawdza za pomocą VAD, czy zawiera ona mowę.

        Jeśli w paczce wykryto głos - resetuje licznik ciszy.
        Jeśli paczka jest cicha - zwiększa licznik ciszy, a po przekroczeniu
        progu VAD_SILENCE_DURATION kończy nagrywanie (is_recording = False).
        """
        # Pobiera pojedynczą paczkę danych audio z karty dźwiękowej i odkłada do RAM
        audio_chunk, error_flag = stream.read(CHUNK_SIZE)
        self.frames.append(audio_chunk)

        flat_audio = audio_chunk.flatten()

        # Wykorzystanie VAD z biblioteki faster-whisper do sprawdzenia,
        # czy w tej konkretnej paczce audio występuje mowa
        timestamps = get_speech_timestamps(
            flat_audio,
            sampling_rate=SAMPLE_RATE,
            threshold = VAD_THRESHOLD,
            min_silence_duration_ms=200
        )

        if len(timestamps) > 0:
            if not self.speech_started:
                logger.info("Wykryłem głos, nagrywam...")
            self.speech_started = True
            self.silence_counter = 0.0
        else:
            # Jeśli funkcja zwróciła pustą listę – mamy ciszę
            chunk_duration = CHUNK_SIZE / SAMPLE_RATE
            self.silence_counter += chunk_duration

            if (self.silence_counter >= VAD_SILENCE_DURATION):
                if (self.speech_started == True):
                    logger.info("Wykryto koniec wypowiedzi (cisza).")
                self.is_recording = False

    def stop_recording(self):
        """Kończy nagrywanie i zwraca scałowane nagranie jako jednowymiarową
        tablicę numpy typu float32. Jeśli nic nie zostało zarejestrowane,
        zwraca pustą tablicę."""
        self.is_recording = False
        if not self.frames:
            return np.zeros(0, dtype=np.float32)
        merged_data = np.concatenate(self.frames, axis=0).flatten()
        return merged_data