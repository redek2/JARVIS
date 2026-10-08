"""
Moduł syntezy mowy (Text-to-Speech) oparty na silniku sherpa-onnx z modelem
głosu VITS (Piper) wytrenowanym dla języka polskiego ("jarvis_wg_glos").
"""
import numpy as np
import re
from scipy import signal
import sherpa_onnx
import sounddevice as sd
import threading

class TTSEngine:
    """Odtwarza tekst na głos, używając lokalnie działającego (offline) modelu
    VITS. Umożliwia również natychmiastowe przerwanie odtwarzania (np. gdy
    użytkownik chce zakończyć program w trakcie mówienia JARVISA)."""
    def __init__(self):
        # Konfiguracja modelu głosu offline (VITS/Piper): plik modelu ONNX,
        # dane fonetyczne espeak-ng oraz plik z mapowaniem tokenów.
        config = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model="voices/vits-piper-pl_PL-jarvis_wg_glos-medium/pl_PL-jarvis_wg_glos-medium.onnx",
                    data_dir="voices/vits-piper-pl_PL-jarvis_wg_glos-medium/espeak-ng-data",
                    tokens="voices/vits-piper-pl_PL-jarvis_wg_glos-medium/tokens.txt",
                ),
                num_threads=4,
            ),
        )
        
        if not config.validate():
            raise ValueError("Please check your config")
        
        self.tts = sherpa_onnx.OfflineTts(config)
        # Flaga wykorzystywana do natychmiastowego przerwania trwającej/kolejnej syntezy mowy
        self.stop_event = threading.Event()

    def ttsInference(self, textToRead):
        """Generuje i odtwarza (synchronicznie, blokująco) mowę dla podanego
        tekstu. Jeśli w międzyczasie wywołano `stop()` lub tekst jest pusty
        bądź zbyt krótki (≤ 1 znak), pomija generowanie."""
        if self.stop_event.is_set():
            return

        textToRead = self._clean_for_tts(textToRead)

        if len(textToRead) <= 1:
            return
        
        # sid=0 - identyfikator głosu (pojedynczy głos w tym modelu); speed=0.8 - lekko spowolnione tempo mówienia
        audio = self.tts.generate(text=textToRead,
                             sid=0,
                             speed=1)

        samples = np.array(audio.samples, dtype=np.float32)

        if audio.sample_rate != 44100:
            num_samples = int(len(samples) * 44100 / audio.sample_rate)
            samples = signal.resample(samples, num_samples)

        silence_padding = np.zeros(int(44100 * 0.25), dtype=np.float32)
        samples_with_padding = np.concatenate([samples, silence_padding])
        
        sd.play(samples_with_padding, samplerate=44100)
        sd.wait()  # blokuje wątek do zakończenia odtwarzania dźwięku

    def stop(self):
        """Natychmiast przerywa aktualnie odtwarzaną mowę i blokuje kolejne
        wywołania `ttsInference` aż do wywołania `reset_stop()`."""
        self.stop_event.set()
        sd.stop()

    def reset_stop(self):
        """Odblokowuje możliwość odtwarzania mowy po wcześniejszym wywołaniu `stop()`."""
        self.stop_event.clear()

    def _clean_for_tts(self, text: str) -> str:
        """Oczyszcza tekst z artefaktów formatowania, które mogą powodować problemy w syntezie mowy (Markdown, fragmenty JSON, znaczniki)."""
        if not text:
            return ""

        # Usuń ewentualne fragmenty JSON/wywołań narzędzi {...}
        clean_text = re.sub(r'\{.*?\}', '', text, flags=re.DOTALL)
        # Usuń znaczniki w nawiasach kątowych i kwadratowych <...>, [...]
        clean_text = re.sub(r'<.*?>|\[.*?\]', '', clean_text)
        
        # Usuń znaczniki Markdown
        clean_text = clean_text.replace('**', "")
        clean_text = clean_text.replace('*', "")
        clean_text = clean_text.replace('```', "")
        clean_text = clean_text.replace('`', "")
        
        return clean_text.strip()