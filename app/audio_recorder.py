import sounddevice as sd
import numpy as np
from app.config import CHUNK_SIZE

class AudioRecorder:
    def __init__(self):
        self.frames = []
        self.is_recording = False
        return None
    
    def start_recording(self):
        # Czyści stare dane i przygotowuje system do zapisu
        self.is_recording = True
        self.frames.clear()
        return None

    def record_chunk(self, stream):
        # Pobiera pojedynczą paczkę danych audio z karty dźwiękowej i odkłada do RAM
        audio_chunk, error_flag = stream.read(CHUNK_SIZE)
        self.frames.append(audio_chunk)
        return None

    def stop_recording(self):
        self.is_recording = False
        merged_data = np.concatenate(self.frames, axis=0).flatten()
        return merged_data