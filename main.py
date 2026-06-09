import threading
from app.audio_recorder import AudioRecorder
from app.stt_engine import STTEngine
import sounddevice as sd
from app.config import SAMPLE_RATE, CHANNELS
from app.llm_engine import LLMEngine

def recording_worker(recorder, stream):
    while (recorder.is_recording == True):
        recorder.record_chunk(stream)

def main():
    recorder = AudioRecorder()
    stt = STTEngine()
    llm = LLMEngine()

    print("\n[JARVIS]: Naciśnij ENTER, aby zacząć mówić...")
    input()
    recorder.start_recording()
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32') as stream:
        t = threading.Thread(target=recording_worker, args=(recorder, stream))
        t.start()
        print("\n[JARVIS]: Nagrywam... Naciśnij ENTER aby zakończyć.")
        input()
        audio_data = recorder.stop_recording()
        print("[JARVIS]: Przetwarzam mowę przez CPU...")
        text_result = stt.transcribe_audio(audio_data)
        print(f"[Użytkownik]: {text_result}")
    
    generator = llm.llmInference(text_result)
    for token in generator:
        print(token, end="", flush=True)

if __name__ == "__main__":
    main()