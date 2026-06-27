import threading
from app.audio_recorder import AudioRecorder
from app.stt.stt_engine import STTEngine
import sounddevice as sd
from app.config import SAMPLE_RATE, CHANNELS, CHUNK_SIZE
from app.llm.llm_engine import LLMEngine
from app.tts.tts_engine import TTSEngine
import time
from colorama import init, Fore, Style
import numpy as np

def recording_worker(recorder, stream):
    while recorder.is_recording and stream.active:
        try:
            recorder.record_chunk(stream)
        except Exception:
            break

def main():
    init(autoreset=True)

    recorder = AudioRecorder()
    stt = STTEngine()
    llm = LLMEngine()
    tts = TTSEngine()

    try:
        print(f"\n{Fore.CYAN}[SYSTEM] System gotowy.{Style.RESET_ALL}")
        sd.play((np.linspace(0.3, 0.0, 4800, False) * np.sin(440 * np.linspace(0, 0.3, 4800, False) * 2 * np.pi)).astype(np.float32), 16000)
        while True:
            recorder.start_recording()
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32', blocksize=CHUNK_SIZE) as stream:
                t = threading.Thread(target=recording_worker, args=(recorder, stream))
                t.start()

                while recorder.is_recording:
                    time.sleep(0.1)

                audio_data = recorder.stop_recording()
                t.join()
            
            if not recorder.speech_started or len(audio_data) == 0:
                continue

            print(f"{Fore.CYAN}[SYSTEM] Przetwarzanie mowy przez CPU.{Style.RESET_ALL}")
            text_result = stt.transcribe_audio(audio_data)
            
            print(f"\n[Użytkownik]: {text_result}")

            if not text_result.strip():
                print(f"{Fore.CYAN}[SYSTEM]: Wykryto ciszę.{Style.RESET_ALL}")
                continue

            print("[JARVIS]: ", end="", flush=True)
            temp = ""
            
            generator = llm.llmInference(text_result)
            for token in generator:
                print(token, end="", flush=True)
                temp += token
            print()

            tts.ttsInference(temp)

    except KeyboardInterrupt:
        print("\nPrzerwano działanie programu z klawiatury.")
    finally:
        print("\nPamięć została wyczyszczona.")

if __name__ == "__main__":
    start = time.perf_counter()
    main()
    end = time.perf_counter()
    print(f"Czas wykonania: {end-start:.1f}s")