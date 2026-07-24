import threading
from app.audio_recorder import AudioRecorder
from app.stt.stt_engine import STTEngine
import sounddevice as sd
from app.config import SAMPLE_RATE, CHANNELS, CHUNK_SIZE, OLLAMA_URL, LLM_MODEL
from app.llm.llm_engine import LLMEngine
from app.tts.tts_engine import TTSEngine
from app.logger import get_logger
import time
import numpy as np
import queue
import re
import random

logger = get_logger(__name__)

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
    recorder = AudioRecorder()
    stt = STTEngine()
    llm = LLMEngine()
    tts = TTSEngine()
    tts_queue = None

    try:
        logger.info("System gotowy.")
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

            logger.info("Przetwarzanie mowy przez CPU.")
            text_result = stt.transcribe_audio(audio_data)

            if not text_result.strip():
                silence_timer += 1
                if silence_timer >= 30:
                    tts.ttsInference("Wykryłem brak aktywności. Przechodzę w tryb uśpienia. Do widzenia.")
                    break
                else:
                    continue

            endings = ["bywaj", "żegnaj", "koniec rozmowy", "dobranoc", "dobra noc", "kończę", "kończymy", "żegnam", "adios", "do zobaczenia"]
            if text_result.strip(" .!?\n").lower() in endings:
                print(f"[Użytkownik]: {text_result}")
                byebye = ["Siemano!", "Do zobaczenia!", "Trzymaj się!", "Cześć!", "Na razie!", "Pa!", "Bywaj!", "Żegnam Pana!", "Pozdrawiam",
                          "Do ponownego zobaczenia!", "Kłaniam się nisko!", "Do następnego!", "Pomyślności!", "Wszystkiego dobrego!", "Z fartem!"]
                tts.ttsInference(random.choice(byebye))
                break

            print(f"\n[Użytkownik]: {text_result}")
            silence_timer = 0

            print("[JARVIS]: ", end="", flush=True)

            tts.reset_stop()

            tts_queue = queue.Queue()
            t_tts = threading.Thread(target=tts_worker, args=(tts, tts_queue), daemon=True)
            t_tts.start()
            
            sentence_buffer = ""
            generator = llm.llmInference(text_result)

            for token in generator:
                print(token, end="", flush=True)
                sentence_buffer += token

                if re.search(r'[.!?\n]\s*$', sentence_buffer):
                    clean_sentence = re.sub(r'\{.*?\}', '', sentence_buffer, flags=re.DOTALL)
                    clean_sentence = re.sub(r'<.*?>|\[.*?\]', '', clean_sentence)

                    clean_sentence = clean_sentence.replace('**', "")
                    clean_sentence = clean_sentence.replace('*', "")
                    clean_sentence = clean_sentence.replace('```', "")

                    if clean_sentence.strip():
                        tts_queue.put(clean_sentence)

                    sentence_buffer = ""

            if sentence_buffer.strip():
                clean_sentence = re.sub(r'\{.*?\}', '', sentence_buffer, flags=re.DOTALL)
                clean_sentence = re.sub(r'<.*?>|\[.*?\]', '', clean_sentence)
                clean_sentence = clean_sentence.replace('**', "").replace('*', "")

                if clean_sentence.strip():
                    tts_queue.put(clean_sentence)

            tts_queue.put(None)
            print()

            t_tts.join()

    except KeyboardInterrupt:
        recorder.stop_recording()
        tts.stop()
        if tts_queue is not None:
            while not tts_queue.empty():
                try:
                    tts_queue.get_nowait()
                    tts_queue.task_done()
                except queue.Empty:
                    break
            tts_queue.put(None)

        logger.info("Przerwano działanie programu z klawiatury.")
    finally:
        if 'llm' in locals() or 'llm' in globals():
            try:
                llm.cleanup()
            except Exception as e:
                logger.error(f"Nie udało się zamknąć silnika LLM: {e}", exc_info=True)
        logger.info("Pamięć została wyczyszczona.")

if __name__ == "__main__":
    start = time.perf_counter()
    main()
    end = time.perf_counter()
    logger.info(f"Czas wykonania: {end-start:.1f}s")