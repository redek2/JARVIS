import sherpa_onnx
import sounddevice as sd

class TTSEngine:
    def __init__(self):
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

    def ttsInference(self, textToRead):
        
        audio = self.tts.generate(text=textToRead,
                             sid=0,
                             speed=1.0)
        
        sd.play(audio.samples, samplerate=audio.sample_rate)
        sd.wait()