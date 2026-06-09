from openai import OpenAI
from app.config import LLM_MODEL
import requests

class LLMEngine:

    def __init__(self):
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama-local",
        )

        # Wywołanie modelu
        requests.post("http://localhost:11434/api/generate", json={"model": LLM_MODEL, "keep_alive": -1})

    def llmInference(self, transcribed_audio):
        stream = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": transcribed_audio
                },
            ],
            stream=True,
        )

        for event in stream:
            yield event.choices[0].delta.content

    def __del__(self):
        try:
            requests.post("http://localhost:11434/api/generate", json={"model": LLM_MODEL, "keep_alive": 0})
        except Exception:
            pass