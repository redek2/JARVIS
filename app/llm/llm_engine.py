from openai import OpenAI
from app.config import LLM_MODEL, OLLAMA_URL
import requests

class LLMEngine:

    def __init__(self):
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama-local",
        )

        # Wywołanie modelu
        requests.post(OLLAMA_URL, json={"model": LLM_MODEL, "keep_alive": -1})

        self.history = [
            {
                "role": "system",
                "content": "Jesteś JARVIS, zaawansowany i genialny asystent sztucznej inteligencji stworzony przez użytkownika."
                "Twoje odpowiedzi powinny być ciepłe, inteligentne, pomocne i uprzejme. Rozmawiasz po polsku."
            }
        ]

    def llmInference(self, transcribed_audio):
        self.history.append({"role": "user", "content": transcribed_audio})


        stream = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=self.history,
            stream=True,
        )
        
        full_response = ""
        for event in stream:
            token = event.choices[0].delta.content
            if token:
                full_response += token
                yield token
        
        if full_response:
            self.history.append({"role": "assistant", "content": full_response})

    def __del__(self):
        try:
            requests.post(OLLAMA_URL, json={"model": LLM_MODEL, "keep_alive": 0})
        except Exception:
            pass