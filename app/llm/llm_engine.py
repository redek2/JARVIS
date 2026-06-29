from openai import OpenAI
from app.config import LLM_MODEL, OLLAMA_URL
import requests
from app.tools.tool_manager import ToolManager
import json
import re

class LLMEngine:

    def __init__(self):
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama-local",
        )

        self.tool_manager = ToolManager()
        self.history = [
            {
                "role": "system",
                "content": """Jesteś JARVIS – polska genialna sztuczna inteligencja. Zwracaj się do użytkownika per Sir lub po imieniu Kamil.
                            Styl:
                            Bądź techniczny i konkretny, utrzymuj ciekawy ton rozmowy.
                            MASZ SPECYFICZNE POCZUCIE HUMORU: Gdy pomysły lub pytania Pana Kamila są absurdalne, niebezpieczne lub dziwne, skomentuj to z lekką, ironiczną szpilką (słabym żartem) bez podchodzenia do analizy.
                            Traktuj szalone pomysły z przymrużeniem oka. Dalej pamiętaj o tym że jesteś AI i wszelkie informacje zewnętrzne wymagają sprawdzenia poprzez narzędzia lub dopytanie użytkownika.

                            Zasady techniczne:
                            1. Pisz wyłącznie czystym tekstem, po polsku.
                            2. Liczby, godziny i daty w finalnej odpowiedzi podawaj słownie.
                            3. Jeśli nie masz pewności co odpowiedzieć, wykorzystaj dostępne narzędzia.
                            4. ZAWSZE wybieraj wykorzystywanie narzędzi ponad historię rozmowy.
                            5. Nie pisz nigdy o zamiarach, tylko działaj.
                            """
            }
        ]

        # Wywołanie modelu
        try:
            native_url = OLLAMA_URL.replace("/v1", "/api/generate")
            requests.post(native_url, json={"model": LLM_MODEL, "prompt": "", "keep_alive": -1}, timeout=10)
        except Exception as e:
            print(f"Nie udało się załadować modelu na starcie: {e}")

    def llmInference(self, transcribed_audio):
        self.history.append({"role": "user", "content": transcribed_audio})


        stream = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=self.history,
            stream=True,
            tools=self.tool_manager.schemas,
        )

        full_response = ""
        tool_id = None
        tool_name = None
        tool_args_chunks = []

        for event in stream:
            delta = event.choices[0].delta

            if hasattr(delta, 'tool_calls') and delta.tool_calls:
                tc = delta.tool_calls[0]
                if tc.id: 
                    tool_id = tc.id
                if tc.function.name: 
                    tool_name = tc.function.name
                if tc.function.arguments: 
                    tool_args_chunks.append(tc.function.arguments)
                continue

            token = delta.content
            if token:
                full_response += token
                yield token

        if tool_name:
            full_arguments_str = "".join(tool_args_chunks)
            try:
                tool_args = json.loads(full_arguments_str or "{}")
            except Exception:
                tool_args = {}

            yield from self._processes_and_execute_tool(tool_id or "call_01", tool_name, tool_args)
            return
        
        if '{"name"' in full_response or '"arguments"' in full_response or "<name>" in full_response:
            try:
                json_match = re.search(r'\{.*\}', full_response, re.DOTALL)
                if json_match:
                    fallback_data = json.loads(json_match.group(0))
                    f_name = fallback_data.get("name")
                    f_args = fallback_data.get("arguments", {})

                    if f_name:
                        yield f"\n[System: wykryto tekstowe wywołanie {f_name}]"
                        yield from self._processes_and_execute_tool("call_01", f_name, json.dumps(f_args), f_args)
                        return
            except Exception:
                pass
                
        if full_response:
            self.history.append({"role": "assistant", "content": full_response})

    def _processes_and_execute_tool(self, tool_id, tool_name, tool_args):

        tool_result = self.tool_manager.execute_tool(tool_name, tool_args)
        #print(f"[DEBUG] Wywołano narzędzie {tool_name}, którego wynik to {tool_result}")

        assistant_tool_msg = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tool_id,
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": json.dumps(tool_args)
                    }
                }
            ]
        }

        self.history.append(assistant_tool_msg)
        self.history.append({
            "role": "system",
            "content": f"[Wywołano narzędzie {tool_name}. Wynik: {tool_result}]"
        })

        second_stream = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=self.history,
            stream=True
        )

        second_full_response = ""
        for second_event in second_stream:
            token = second_event.choices[0].delta.content
            if token:
                second_full_response += token
                yield token
        
        if second_full_response:
            self.history.append({"role": "assistant", "content": second_full_response})

    def cleanup(self):
        try:
            response = requests.post(OLLAMA_URL.replace("/v1", "/api/generate"), json={"model": LLM_MODEL, "keep_alive": 0})
        except Exception as e:
            print(f"Błąd podczas zwalniania VRAM: {e}")