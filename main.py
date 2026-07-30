"""
Punkt wejścia asystenta głosowego JARVIS.

Główna pętla programu realizuje cykl:
    1. Nagrywanie mowy użytkownika z wykrywaniem aktywności głosowej (VAD).
    2. Transkrypcja nagrania na tekst (STT).
    3. Wysłanie tekstu do modelu językowego (LLM), który odpowiada strumieniowo
       i w razie potrzeby korzysta z narzędzi (np. podanie godziny, przeszukanie Notion).
    4. Odczytanie odpowiedzi na głos (TTS) zdanie po zdaniu, równolegle do generowania
       kolejnych tokenów przez LLM.

Nagrywanie audio, generowanie odpowiedzi LLM i synteza mowy działają
w osobnych wątkach, aby TTS mogło zacząć czytać pierwsze zdanie zanim
LLM skończy generować całą odpowiedź.
"""
import threading
from app.audio_recorder import AudioRecorder
from app.stt.stt_engine import STTEngine
import sounddevice as sd
from app.config import SAMPLE_RATE, CHANNELS, CHUNK_SIZE, SILENCE_TIMER
from app.llm.llm_engine import LLMEngine
from app.tts.tts_engine import TTSEngine
from app.logger import get_logger
from app.asphalt import recording_worker, tts_worker, InactivityTracker
import time
import numpy as np
import queue
import re
import random

logger = get_logger(__name__)     

def main():
    """Główna funkcja programu: inicjalizuje silniki (STT, LLM, TTS, rejestrator
    audio), a następnie uruchamia nieskończoną pętlę konwersacji głos-tekst-głos,
    aż do wykrycia frazy pożegnalnej, dłuższej ciszy (tryb uśpienia) lub
    przerwania z klawiatury (Ctrl+C)."""
    try:
        recorder = AudioRecorder()
        stt = STTEngine()
        llm = LLMEngine()
        tts = TTSEngine()
        tracker = InactivityTracker()
    except KeyboardInterrupt:
        logger.info("Przerwano działanie programu z klawiatury.")
        return
    except Exception as e:
        logger.error(f"Wystąpił błąd podczas inicjalizacji: {e}", exc_info=True)
        return
    tts_queue = None

    try:
        logger.info("System gotowy.")
        # Krótki dźwiękowy sygnał (opadający ton 440 Hz) informujący użytkownika, że system wystartował.
        sd.play((np.linspace(0.3, 0.0, 4800, False) * np.sin(440 * np.linspace(0, 0.3, 4800, False) * 2 * np.pi)).astype(np.float32), 16000)
        unload_timer = time.perf_counter()
        while True:
            try:
                tts_queue = None
                # --- 1. Nagrywanie ---
                recorder.start_recording()
                with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32', blocksize=CHUNK_SIZE) as stream:
                    # Nagrywanie odbywa się w osobnym wątku, aby pętla główna mogła
                    # jednocześnie czekać na zakończenie wypowiedzi (recorder.is_recording == False)
                    t = threading.Thread(target=recording_worker, args=(recorder, stream), daemon=True)
                    t.start()

                    try:
                        while recorder.is_recording:
                            time.sleep(0.1)
                        audio_data = recorder.stop_recording()
                    finally:
                        recorder.is_recording = False
                        t.join()
                
                # Brak wykrytej mowy (VAD) lub puste nagranie - zwiększ licznik ciszy i ewentualnie uśpij system
                if not recorder.speech_started or len(audio_data) == 0:
                    elapsed = time.perf_counter() - unload_timer
                    remaining = SILENCE_TIMER - elapsed
                    tracker.inactivity_worker(remaining)
                    if elapsed >= SILENCE_TIMER:
                        tts.ttsInference("Wykryłem brak aktywności. Przechodzę w tryb uśpienia.")
                        break
                    else:
                        continue

                # --- 2. Transkrypcja mowy na tekst (STT) ---
                logger.info("Przetwarzanie mowy przez CPU.")
                text_result = stt.transcribe_audio(audio_data)

                # Whisper nie rozpoznał żadnego tekstu - traktuj jak ciszę
                if not text_result.strip():
                    elapsed = time.perf_counter() - unload_timer
                    remaining = SILENCE_TIMER - elapsed
                    tracker.inactivity_worker(remaining)
                    if elapsed >= SILENCE_TIMER:
                        tts.ttsInference("Wykryłem brak aktywności. Przechodzę w tryb uśpienia. Do widzenia.")
                        break
                    else:
                        continue

                # Rozpoznanie frazy kończącej rozmowę - jeśli użytkownik pożegnał się, zakończ pętlę
                endings = ["bywaj", "żegnaj", "koniec rozmowy", "dobranoc", "dobra noc", "kończę", "kończymy", "żegnam", "adios", "do zobaczenia"]
                if text_result.strip(" .!?\n").lower() in endings:
                    print(f"[Użytkownik]: {text_result}")
                    byebye = ["Siemano!", "Do zobaczenia!", "Trzymaj się!", "Cześć!", "Na razie!", "Pa!", "Bywaj!", "Żegnam Pana!", "Pozdrawiam",
                            "Do ponownego zobaczenia!", "Kłaniam się nisko!", "Do następnego!", "Pomyślności!", "Wszystkiego dobrego!", "Z fartem!"]
                    tts.ttsInference(random.choice(byebye))
                    break

                print(f"\n[Użytkownik]: {text_result}")

                print("[JARVIS]: ", end="", flush=True)

                tts.reset_stop()

                # --- 3. Generowanie odpowiedzi (LLM) i równoległe odtwarzanie (TTS) ---
                # Kolejka pośredniczy między wątkiem generującym tekst a wątkiem czytającym go na głos,
                # dzięki czemu TTS może zacząć mówić pierwsze zdanie zanim LLM skończy całą odpowiedź.
                tts_queue = queue.Queue()
                t_tts = threading.Thread(target=tts_worker, args=(tts, tts_queue), daemon=True)
                t_tts.start()
                
                sentence_buffer = ""
                generator = llm.llmInference(text_result + "\nOdpowiedz krótko")

                # LLM zwraca tekst strumieniowo (token po tokenie). Bufor składamy w zdania -
                # każde zakończone znakiem interpunkcyjnym (. ! ? lub nową linią) zdanie jest
                # oczyszczane z artefaktów formatowania (Markdown, znaczniki narzędzi) i wysyłane
                # do kolejki TTS, aby móc je odczytać zanim reszta odpowiedzi zostanie wygenerowana.
                for token in generator:
                    print(token, end="", flush=True)
                    sentence_buffer += token

                    if re.search(r'[.!?\n]\s*$', sentence_buffer):
                        # Usuń ewentualne fragmenty JSON/wywołań narzędzi oraz znaczniki w nawiasach kłątkowych/ostrych
                        clean_sentence = re.sub(r'\{.*?\}', '', sentence_buffer, flags=re.DOTALL)
                        clean_sentence = re.sub(r'<.*?>|\[.*?\]', '', clean_sentence)

                        # Usuń znaczniki Markdown, których syntezator mowy nie powinien czytać na głos
                        clean_sentence = clean_sentence.replace('**', "")
                        clean_sentence = clean_sentence.replace('*', "")
                        clean_sentence = clean_sentence.replace('```', "")
                        clean_sentence = clean_sentence.replace('`', "")

                        if clean_sentence.strip():
                            tts_queue.put(clean_sentence)

                        sentence_buffer = ""

                # Ostatni, niedomknięty fragment odpowiedzi (bez końcowej interpunkcji) również trzeba przeczytać
                if sentence_buffer.strip():
                    clean_sentence = re.sub(r'\{.*?\}', '', sentence_buffer, flags=re.DOTALL)
                    clean_sentence = re.sub(r'<.*?>|\[.*?\]', '', clean_sentence)
                    clean_sentence = clean_sentence.replace('**', "").replace('*', "")

                    if clean_sentence.strip():
                        tts_queue.put(clean_sentence)

                tts_queue.put(None)
                print()

                t_tts.join()
                unload_timer = time.perf_counter()
                tracker = InactivityTracker()
            except Exception as e:
                logger.error(f"Wystąpił błąd: {e}", exc_info=True)
                recorder.stop_recording()
                if tts_queue is not None:
                    tts.stop()
                    tts_queue.put(None)
                    t_tts.join()
                continue

    except KeyboardInterrupt:
        # Użytkownik przerwał program (Ctrl+C) - zatrzymaj nagrywanie i odtwarzanie,
        # a następnie wyczyść kolejkę TTS i poślij sygnał zakończenia do wątku TTS.
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
        # Niezależnie od sposobu zakończenia pętli - zwolnij zasoby silnika LLM
        # (np. wyładuj model z pamięci Ollamy, jeśli był używany lokalny provider).
        if 'llm' in locals():
            try:
                llm.cleanup()
            except Exception as e:
                logger.error(f"Nie udało się zamknąć silnika LLM: {e}", exc_info=True)
        logger.info("Pamięć została wyczyszczona.")

if __name__ == "__main__":
    # Uruchomienie programu i pomiar całkowitego czasu działania (do logów diagnostycznych)
    start = time.perf_counter()
    main()
    end = time.perf_counter()
    logger.info(f"Czas wykonania: {end-start:.1f}s")