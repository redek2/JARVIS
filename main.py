import threading
from app.audio_recorder import AudioRecorder
from app.stt.stt_engine import STTEngine
import sounddevice as sd
from app.config import SAMPLE_RATE, CHANNELS, CHUNK_SIZE, OLLAMA_URL, LLM_MODEL
from app.llm.llm_engine import LLMEngine
from app.tts.tts_engine import TTSEngine
import time
from colorama import init, Fore, Style
import numpy as np
import queue
import re

def recording_worker(recorder, stream):
    while recorder.is_recording and stream.active:
        try:
            recorder.record_chunk(stream)
        except Exception:
            break

def tts_worker(tts_engine, tts_queue):
    while True:
        sentence = tts_queue.get()
        if sentence is None:
            tts_queue.task_done()
            break

        tts_engine.ttsInference(sentence)
        tts_queue.task_done()

def main():
    init(autoreset=True)

    recorder = AudioRecorder()
    stt = STTEngine()
    llm = LLMEngine()
    tts = TTSEngine()

    try:
        print(f"\n{Fore.CYAN}[SYSTEM] System gotowy.{Style.RESET_ALL}")
        sd.play((np.linspace(0.3, 0.0, 4800, False) * np.sin(440 * np.linspace(0, 0.3, 4800, False) * 2 * np.pi)).astype(np.float32), 16000)
        silence_timer = 0
        while True:
            recorder.start_recording()
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32', blocksize=CHUNK_SIZE) as stream:
                t = threading.Thread(target=recording_worker, args=(recorder, stream), daemon=True)
                t.start()

                while recorder.is_recording:
                    time.sleep(0.1)

                audio_data = recorder.stop_recording()
                t.join()
            
            if not recorder.speech_started or len(audio_data) == 0:
                silence_timer += 1
                if silence_timer >= 30:
                    tts.ttsInference("Wykryłem brak aktywności. Przechodzę w tryb uśpienia.")
                    break
                else:
                    continue

            print(f"{Fore.CYAN}[SYSTEM] Przetwarzanie mowy przez CPU.{Style.RESET_ALL}")
            text_result = stt.transcribe_audio(audio_data)

            if not text_result.strip():
                silence_timer += 1
                if silence_timer >= 30:
                    tts.ttsInference("Wykryłem brak aktywności. Przechodzę w tryb uśpienia. Do widzenia.")
                    break
                else:
                    continue

            endings = ["bywaj", "żegnaj", "koniec rozmowy", "dobranoc"]
            if text_result.strip(" .!?\n").lower() in endings:
                print(f"[Użytkownik]: {text_result}")
                tts.ttsInference("Żegnam pana!")
                break

            print(f"\n[Użytkownik]: {text_result}")
            silence_timer = 0

            print("[JARVIS]: ", end="", flush=True)

            tts_queue = queue.Queue()
            t_tts = threading.Thread(target=tts_worker, args=(tts, tts_queue), daemon=True)
            t_tts.start()
            
            sentence_buffer = ""
            generator = llm.llmInference(text_result)

            for token in generator:
                print(token, end="", flush=True)
                sentence_buffer += token

                if re.search(r'[.!?\n]\s*$', sentence_buffer):
                    tts_queue.put(sentence_buffer)
                    sentence_buffer = ""

            if sentence_buffer.strip():
                tts_queue.put(sentence_buffer)

            tts_queue.put(None)
            print()

            t_tts.join()

    except KeyboardInterrupt:
        sd.stop()
        print("\nPrzerwano działanie programu z klawiatury.")
    finally:
        if 'llm' in locals() or 'llm' in globals():
            try:
                llm.cleanup()
            except Exception as e:
                print(f"Nie udało się zamknąć silnika LLM: {e}")
        print("\nPamięć została wyczyszczona.")

if __name__ == "__main__":
    start = time.perf_counter()
    main()
    end = time.perf_counter()
    print(f"Czas wykonania: {end-start:.1f}s")