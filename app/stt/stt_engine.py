"""
Moduł rozpoznawania mowy (Speech-to-Text) oparty na bibliotece faster-whisper.
"""
from faster_whisper import WhisperModel
from app.config import STT_MODEL_SIZE, SAMPLE_RATE
from app.logger import get_logger
from scipy import signal
import time

logger = get_logger(__name__)

class STTEngine:
    """Opakowuje model Whisper i udostępnia prostą metodę do transkrypcji
    nagranego audio na tekst w języku polskim."""
    def __init__(self):
        # Model działa na CPU z kwantyzacją int8 (szybsze, mniejsze zużycie pamięci
        # kosztem niewielkiej utraty precyzji) i wykorzystuje 4 wątki procesora.
        self.model = WhisperModel(
            STT_MODEL_SIZE, 
            device="cpu", 
            compute_type="int8", 
            cpu_threads=4
        )
    
    def transcribe_audio(self, audio_data):
        """Transkrybuje przekazane audio na tekst w języku polskim."""
        if len(audio_data) == 0:
            return ""

        # Resampling audio do 16000 Hz jeśli nagrywamy w innej częstotliwości (np. 44100 Hz)
        if SAMPLE_RATE != 16000:
            t_resample_start = time.perf_counter()
            num_samples = int(len(audio_data) * 16000 / SAMPLE_RATE)
            audio_data = signal.resample(audio_data, num_samples)
            resample_duration = time.perf_counter() - t_resample_start
            logger.info(f"Różnica czasu wynosi: {resample_duration:.3f}s")

        another_start = time.perf_counter()
        segments, info = self.model.transcribe(
            audio_data,
            beam_size=5,
            language="pl",
            vad_filter=True,
            initial_prompt="Asystent Jarvis. Kamil rozmawia z Jarvisem."
        )

        final_text = ""
        for segment in segments:
            final_text += segment.text
        whisper_duration = time.perf_counter() - another_start
        logger.info(f"Czas inferencji faster-whisper: {whisper_duration:.3f}s")
        return final_text
