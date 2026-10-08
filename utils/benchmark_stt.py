"""
Benchmark porównawczy silników STT: faster-whisper vs pywhispercpp (whisper.cpp).
"""

import time
import numpy as np
import sherpa_onnx
from faster_whisper import WhisperModel
from pywhispercpp.model import Model as WhisperCppModel
from scipy.io import wavfile
from scipy import signal

AUDIO_PATH = "sample_pl.wav"

def benchmark_whisper_onnx():
    print("\n--- Test: sherpa-onnx (Whisper-Small greedy) ---")
    recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder="models/stt_whisper_onnx/small-encoder.int8.onnx",
        decoder="models/stt_whisper_onnx/small-decoder.int8.onnx",
        tokens="models/stt_whisper_onnx/small-tokens.txt",
        language="pl",
        decoding_method="greedy_search",
        tail_paddings=1000,
        num_threads=4,
    )

    t_start = time.perf_counter()
    stream = recognizer.create_stream()

    import soundfile as sf
    audio_data, sample_rate = sf.read(AUDIO_PATH, dtype="float32")

    if sample_rate != 16000:
        num_samples = int(len(audio_data) * 16000 / sample_rate)
        audio_data = signal.resample(audio_data, num_samples)
        sample_rate = 16000

        silence = np.zeros(int(sample_rate * 0.5), dtype=np.float32)
        audio_data = np.concatenate([audio_data, silence])
        
    stream.accept_waveform(sample_rate, audio_data)
    recognizer.decode_stream(stream)
    text = stream.result.text
    t_duration = time.perf_counter() - t_start

    print(f"Tekst: '{text.strip()}'")
    print(f"Czas wykonania: {t_duration:.2f}s")
    return t_duration

def benchmark_faster_whisper():
    print("\n--- Test: faster-whisper (small, int8) ---")
    samplerate, audio_data = wavfile.read(AUDIO_PATH)
    if audio_data.dtype != np.float32:
        audio_data = audio_data.astype(np.float32) / 32768.0

    model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)

    t_start = time.perf_counter()
    segments, _ = model.transcribe(audio_data, language="pl", beam_size=5)
    text = "".join([segment.text for segment in segments])
    t_duration = time.perf_counter() - t_start

    print(f"Tekst: '{text.strip()}'")
    print(f"Czas wykonania: {t_duration:.2f}s")
    return t_duration

def benchmark_whisper_cpp():
    print("\n--- Test: pywhispercpp (small-q5_1) ---")
    model = WhisperCppModel('small-q5_1', n_threads=4, print_realtime=False, print_progress=False)

    samplerate, audio_data = wavfile.read(AUDIO_PATH)
    if samplerate != 16000:
        num_samples = int(len(audio_data) * 16000 / samplerate)
        audio_data = signal.resample(audio_data, num_samples)
        samplerate = 16000

    if audio_data.dtype == np.float32:
        audio_int16 = (np.clip(audio_data, -1.0, 1.0) * 32767).astype(np.int16)
    else:
        audio_int16 = audio_data.astype(np.int16)
        
    wavfile.write(AUDIO_PATH, samplerate, audio_int16)

    t_start = time.perf_counter()
    segments = model.transcribe(AUDIO_PATH, language="pl")
    text = "".join([seg.text for seg in segments])
    t_duration = time.perf_counter() - t_start

    print(f"Tekst: '{text.strip()}'")
    print(f"Czas wykonania: {t_duration:.2f}s")
    return t_duration

if __name__ == "__main__":
    t_fw = benchmark_faster_whisper()
    t_cpp = benchmark_whisper_cpp()
    t_onnx = benchmark_whisper_onnx()

    print("\n=== PODSUMOWANIE ===")
    print(f"faster-whisper: {t_fw:.2f}s")
    print(f"whisper.cpp: {t_cpp:.2f}s")
    print(f"Whisper onnx: {t_onnx:.2f}s")
    #print(f"Przyspieszenie: {t_fw / t_cpp:.2f}x")