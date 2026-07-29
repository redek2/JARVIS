from app.config import SILENCE_TIMER
from app.logger import get_logger

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

class InactivityTracker():
    def __init__(self):
        self.milestones = [60, 30, 15, 10, 5, 4, 3, 2 , 1]
        while self.milestones and SILENCE_TIMER <= self.milestones[0]:
            self.milestones.pop(0)

    def inactivity_worker(self, remaining):
        if self.milestones != [] and remaining <= self.milestones[0]:
            logger.info(f"Do zamknięcia programu zostało: {remaining:.0f} sekund.")
            self.milestones.pop(0)
