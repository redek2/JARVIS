"""
Moduł rozpoznawania mowy (Speech-to-Text) oparty na bibliotece faster-whisper.
"""
from faster_whisper import WhisperModel
from app.config import STT_MODEL_SIZE

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
        """Transkrybuje przekazane audio (numpy array, 16 kHz, mono) na tekst
        w języku polskim. Wykorzystuje wewnętrzny filtr VAD Whispera
        (vad_filter=True), aby pominąć fragmenty ciszy, oraz beam search
        (beam_size=5) dla dokładniejszej transkrypcji. Zwraca połączony
        tekst ze wszystkich rozpoznanych segmentów."""
        segments, info = self.model.transcribe(audio_data, beam_size=5, language="pl", vad_filter=True)
        final_text = ""
        for segment in segments:
            final_text += segment.text
        return final_text