"""
Moduł syntezy mowy (Text-to-Speech) oparty na silniku sherpa-onnx z modelem
głosu VITS (Piper) wytrenowanym dla języka polskiego ("jarvis_wg_glos").
"""
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

        if not textToRead or not textToRead.strip() or len(textToRead.strip()) <= 1:
            return
        
        # sid=0 - identyfikator głosu (pojedynczy głos w tym modelu); speed=0.8 - lekko spowolnione tempo mówienia
        audio = self.tts.generate(text=textToRead,
                             sid=0,
                             speed=0.8)
        
        sd.play(audio.samples, samplerate=audio.sample_rate)
        sd.wait()  # blokuje wątek do zakończenia odtwarzania dźwięku

    def stop(self):
        """Natychmiast przerywa aktualnie odtwarzaną mowę i blokuje kolejne
        wywołania `ttsInference` aż do wywołania `reset_stop()`."""
        self.stop_event.set()
        sd.stop()

    def reset_stop(self):
        """Odblokowuje możliwość odtwarzania mowy po wcześniejszym wywołaniu `stop()`."""
        self.stop_event.clear()