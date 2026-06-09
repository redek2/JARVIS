from faster_whisper import WhisperModel
from app.config import STT_MODEL_SIZE

class STTEngine:
    def __init__(self):
        self.model = WhisperModel(
            STT_MODEL_SIZE, 
            device="cpu", 
            compute_type="int8", 
            cpu_threads=4
        )
        return None
    
    def transcribe_audio(self, audio_data):
        segments, info = self.model.transcribe(audio_data, beam_size=5, language="pl", vad_filter=True)
        final_text = ""
        for segment in segments:
            final_text += segment.text
        return final_text