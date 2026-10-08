from app.config import SILENCE_TIMER
from app.logger import get_logger
import soundfile as sf
import sounddevice as sd
import threading
import time

logger = get_logger(__name__)     

def recording_worker(recorder, stream):
    """Wątek pomocniczy: w pętli pobiera kolejne paczki audio ze strumienia
    mikrofonu i przekazuje je do rejestratora (AudioRecorder), dopóki trwa
    nagrywanie i strumień jest aktywny. Wyjątki (np. zamknięcie strumienia)
    przerywają pętlę bez propagowania błędu do wątku głównego."""
    while recorder.is_recording and stream.active:
        try:
            recorder.record_chunk(stream)
        except Exception as e:
            logger.error(f"Worker wyrzucił błąd: {e}", exc_info=True)
            break

def tts_worker(tts_engine, tts_queue):
    """Wątek pomocniczy odpowiedzialny za odtwarzanie mowy (TTS).

    Pobiera z kolejki kolejne gotowe zdania i odczytuje je na głos.
    Wstawienie wartości None do kolejki jest sygnałem zakończenia pracy
    wątku (odpowiednik komunikatu 'koniec strumienia').
    """
    while True:
        sentence = tts_queue.get()
        if sentence is None:
            tts_queue.task_done()
            break

        tts_engine.ttsInference(sentence)
        tts_queue.task_done()

def play_loop_audio_worker(file_path: str, stop_event: threading.Event):
    try:
        data, fs = sf.read(file_path, dtype='float32')
        while not stop_event.is_set():
            sd.play(data, fs)
            while sd.get_stream() and sd.get_stream().active:
                if stop_event.is_set():
                    sd.stop()
                    break
            time.sleep(0.05)
    except Exception as e:
        logger.error(f"Nie udało się odtworzyć pliku audio: {e}", exc_info=True)

def play_audio_worker(file_path: str):
    try:
        data, fs = sf.read(file_path, dtype='float32')
        data *= 0.15
        sd.play(data, fs)
        sd.wait()  # blokuje wątek do zakończenia odtwarzania dźwięku
    except Exception as e:
        logger.error(f"Nie udało się odtworzyć pliku audio: {e}", exc_info=True)

class InactivityTracker():
    def __init__(self):
        self.milestones = [60, 30, 15, 10, 5, 4, 3, 2 , 1]
        while self.milestones and SILENCE_TIMER <= self.milestones[0]:
            self.milestones.pop(0)

    def inactivity_worker(self, remaining):
        if self.milestones != [] and remaining <= self.milestones[0]:
            logger.info(f"Do zamknięcia programu zostało: {remaining:.0f} sekund.")
            self.milestones.pop(0)
