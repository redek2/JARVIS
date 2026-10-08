"""
Skrypt pomocniczy do wygenerowania próbki mowy .wav na potrzeby benchmarku STT.
"""
import numpy as np
from app.tts.tts_engine import TTSEngine
from scipy.io import wavfile

def create_sample():
    print("Inicjalizacja TTS...")
    tts_engine = TTSEngine()
    text = "Podaj aktualną godzinę i datę."

    print(f"Generowanie mowy dla tekstu: {text}")
    audio = tts_engine.tts.generate(text=text, sid=0, speed=1.0)

    samples = np.array(audio.samples, dtype=np.float32)
    sample_rate = audio.sample_rate

    output_filename = "sample_pl.wav"
    wavfile.write(output_filename, sample_rate, samples)
    print(f"Pomyślnie zapisano plik testowy: {output_filename}")

if __name__ == "__main__":
    create_sample()