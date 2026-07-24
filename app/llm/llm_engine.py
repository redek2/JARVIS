from openai import OpenAI
from app.config import LLM_MODEL, OLLAMA_URL, SYSTEM_PROMPT, LLM_PROVIDER, LLM_TEMPERATURE, LLM_MAX_TOKENS, GROQ_BASE_URL, GROQ_MODEL
import requests
from app.tools.tool_manager import ToolManager
import json
import re
import copy
import os
from dotenv import load_dotenv
from app.logger import get_logger

load_dotenv()
logger = get_logger(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("Brak klucza API GROQ w zmiennych środowiskowych. Upewnij się, że plik .env zawiera poprawny klucz.")

class LLMEngine:

    def __init__(self):
        self.tool_manager = ToolManager()
        self.history = copy.deepcopy(SYSTEM_PROMPT)

        if (LLM_PROVIDER == "groq"):
            self.client = OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY)
            self.model = GROQ_MODEL
        elif (LLM_PROVIDER == "ollama"):
            self.client = OpenAI(base_url=OLLAMA_URL, api_key="ollama-local")
            self.model = LLM_MODEL
            self._warmup_model()

    def llmInference(self, transcribed_audio):
        self.history.append({"role": "user", "content": transcribed_audio})

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                stream=True,
                tools=self.tool_manager.schemas,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS
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
        except Exception as e:
            logger.error(f"Błąd połączenia z LLM: {e}", exc_info=True)
            if self.history and self.history[-1]["role"] == "user":
                self.history.pop()  # Usuń ostatnią wiadomość użytkownika, jeśli wystąpił błąd
            yield "Przepraszam Sir, wystąpił problem z połączeniem z silnikiem językowym."
            return

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
                        yield from self._processes_and_execute_tool("call_01", f_name, f_args)
                        return
            except Exception:
                pass
                
        if full_response:
            self.history.append({"role": "assistant", "content": full_response})

    def _processes_and_execute_tool(self, tool_id, tool_name, tool_args):

        tool_result = self.tool_manager.execute_tool(tool_name, tool_args)

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
            "role": "tool",
            "tool_call_id": tool_id,
            "content": str(tool_result)
        })

        try:
            second_stream = self.client.chat.completions.create(
                model=self.model,
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
        except Exception as e:
            logger.error(f"Błąd połączenia z LLM podczas drugiego strumienia: {e}", exc_info=True)
            if len(self.history) >= 2:
                self.history.pop()  # Usuń wiadomość roli "tool"
                self.history.pop()  # Usuń wiadomość roli "assistant" (tool call)
            yield "Przepraszam Sir, wystąpił problem z połączeniem z silnikiem językowym podczas przetwarzania narzędzia."
            return

    def cleanup(self):
        if LLM_PROVIDER == "ollama":
            self._unload_model()

    def _warmup_model(self):
        try:
            response = requests.post(OLLAMA_URL.replace("/v1", "/api/generate"), json={"model": LLM_MODEL, "prompt": "", "keep_alive": -1}, timeout=10)
        except Exception as e:
            logger.warning(f"Nie udało się załadować modelu na starcie: {e}", exc_info=True)

    def _unload_model(self):
        try:
            response = requests.post(OLLAMA_URL.replace("/v1", "/api/generate"), json={"model": LLM_MODEL, "keep_alive": 0})
        except Exception as e:
            logger.warning(f"Nie udało się zwolnić modelu: {e}", exc_info=True)