"""
Silnik modelu językowego (LLM) - serce logiki konwersacyjnej JARVISA.

Odpowiada za:
    - utrzymywanie historii rozmowy (z ograniczonym budżetem tokenów),
    - komunikację z dostawcą LLM (Groq lub lokalna Ollama) przez API zgodne z OpenAI,
    - strumieniowe generowanie odpowiedzi (token po tokenie),
    - wykrywanie i wykonywanie wywołań narzędzi (function calling) zdefiniowanych
      w ToolManager, wraz z obsługą "awaryjnego" parsowania wywołań narzędzi,
      gdy model zwróci je jako zwykły tekst zamiast ustrukturyzowanego tool_call.
"""
from openai import OpenAI
from app.config import LLM_MODEL, OLLAMA_URL, SYSTEM_PROMPT, LLM_PROVIDER, LLM_TEMPERATURE, LLM_MAX_TOKENS, GROQ_BASE_URL, GROQ_MODEL, LLM_FREQUENCY_PENALTY, MAX_HISTORY_TOKENS
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
class LLMEngine:
    """Otacza klienta OpenAI-compatible (Groq lub Ollama) i zarządza pełnym
    cyklem życia jednej rozmowy: historią wiadomości, strumieniowaniem
    odpowiedzi oraz wywoływaniem narzędzi (tools) na żądanie modelu."""

    def __init__(self):
        """Inicjalizuje menedżera narzędzi, historię rozmowy (zaczynającą się
        od promptu systemowego z config.py) oraz klienta API właściwego dla
        wybranego dostawcy LLM (Groq lub lokalna Ollama)."""
        self.tool_manager = ToolManager()
        self.history = copy.deepcopy(SYSTEM_PROMPT)

        if (LLM_PROVIDER == "groq"):
            self.client = OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY)
            self.model = GROQ_MODEL
            if not GROQ_API_KEY:
                raise RuntimeError("Brak klucza API GROQ w zmiennych środowiskowych. Upewnij się, że plik .env zawiera poprawny klucz.")
        elif (LLM_PROVIDER == "ollama"):
            self.client = OpenAI(base_url=OLLAMA_URL, api_key="ollama-local")
            self.model = LLM_MODEL
            self._warmup_model()  # dla Ollamy: załaduj model do pamięci od razu, aby uniknąć opóźnienia przy pierwszym zapytaniu

    def llmInference(self, transcribed_audio):
        """Generator: wysyła wypowiedź użytkownika do LLM i strumieniowo zwraca
        (yield) kolejne fragmenty (tokeny) tekstowej odpowiedzi.

        Jeśli model zdecyduje się wywołać narzędzie (tool call), wykonuje je
        i kontynuuje strumieniowanie w drugim, kolejnym zapytaniu do modelu
        (patrz `_processes_and_execute_tool`). W przypadku błędu połączenia
        zwraca (yield) komunikat o problemie i wycofuje ostatnią wiadomość
        użytkownika z historii, aby nie została błędnie utrwalona.
        """
        self.history.append({"role": "user", "content": transcribed_audio})
        self._trim_history()

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                stream=True,
                tools=self.tool_manager.schemas,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
                frequency_penalty=LLM_FREQUENCY_PENALTY
            )

            full_response = ""
            tool_dict = {} # {"index": [id, name, arguments]}

            # Odczytuj kolejne "kawałki" (delty) odpowiedzi ze strumienia.
            # Model może zwracać albo zwykły tekst, albo (fragmentarycznie) wywołanie narzędzia -
            # w tym drugim przypadku składamy nazwę narzędzia i jego argumenty z kolejnych fragmentów.
            for event in stream:
                delta = event.choices[0].delta

                if hasattr(delta, 'tool_calls') and delta.tool_calls:
                    for tc in delta.tool_calls:
                        if tc.index is not None and tc.index not in tool_dict:
                            tool_dict[tc.index] = {"id": None, "name": None, "args": []}
                        if tc.id: 
                            tool_dict[tc.index]["id"] = tc.id
                        if tc.function.name: 
                            tool_dict[tc.index]["name"] = tc.function.name
                        if tc.function.arguments: 
                            tool_dict[tc.index]["args"].append(tc.function.arguments)
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

        # Model poprosił o wywołanie narzędzia (ustrukturyzowany tool_call) - wykonaj je
        # i przekaż wynik z powrotem do modelu, aby dokończył odpowiedź.
        if tool_dict:
            yield from self._processes_and_execute_tool(tool_dict)
            return
        
        # Zabezpieczenie awaryjne: niektóre modele (zwłaszcza mniejsze lokalne)
        # potrafią zamiast poprawnego tool_call zwrócić wywołanie narzędzia
        # jako zwykły tekst w formacie JSON. Wykryj taką sytuację i obsłuż ją tak samo.
        if '{"name"' in full_response or '"arguments"' in full_response or "<name>" in full_response:
            try:
                json_match = re.search(r'\{.*\}', full_response, re.DOTALL)
                if json_match:
                    fallback_data = json.loads(json_match.group(0))
                    f_name = fallback_data.get("name")
                    f_args = fallback_data.get("arguments", {})

                    if f_name:
                        yield f"\n[System: wykryto tekstowe wywołanie {f_name}]"
                        yield from self._processes_and_execute_tool({0: {"id": "call_01", "name": f_name, "args": [json.dumps(f_args)]}})
                        return
            except Exception:
                pass
                
        # Zwykła odpowiedź tekstowa (bez użycia narzędzia) - zapisz ją w historii rozmowy
        if full_response:
            self.history.append({"role": "assistant", "content": full_response})

    def _processes_and_execute_tool(self, tool_dict):
        """Wykonuje wskazane narzędzie, zapisuje w historii zarówno żądanie
        wywołania (rola 'assistant' z tool_calls), jak i jego wynik (rola 'tool'),
        a następnie wysyła drugie zapytanie do modelu, aby ten sformułował
        naturalnojęzykową odpowiedź na podstawie wyniku narzędzia. Zwraca
        (yield) strumień tokenów tej końcowej odpowiedzi.
        """
        tool_calls_list = []
        tool_result_list = []

        for tool in tool_dict:
            full_arguments_str = "".join(tool_dict[tool]["args"])
            try:
                tool_args = json.loads(full_arguments_str or "{}")
            except Exception:
                tool_args = {}
            tool_calls_list.append({
                "id": tool_dict[tool]["id"],
                "type": "function",
                "function": {
                    "name": tool_dict[tool]["name"],
                    "arguments": "".join(tool_dict[tool]["args"])
                }
            })
            tool_result = self.tool_manager.execute_tool(tool_dict[tool]["name"], tool_args)
            tool_result_list.append({
                "role": "tool",
                "tool_call_id": tool_dict[tool]["id"],
                "content": str(tool_result)
            })

        assistant_tool_msg = {
            "role": "assistant",
            "content": None,
            "tool_calls": tool_calls_list
        }
        
        self.history.append(assistant_tool_msg)
        self.history.extend(tool_result_list)

        self._trim_history()

        try:
            # Drugie zapytanie do modelu - tym razem BEZ listy narzędzi (tools),
            # żeby wymusić sformułowanie ostatecznej, naturalnojęzykowej odpowiedzi
            # zamiast kolejnego wywołania narzędzia.
            second_stream = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                stream=True,
                max_tokens=LLM_MAX_TOKENS,
                frequency_penalty=LLM_FREQUENCY_PENALTY
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
        """Zwalnia zasoby silnika LLM przy zamykaniu aplikacji. Dotyczy tylko
        dostawcy Ollama - Groq jest usługą zewnętrzną i nie wymaga zwalniania."""
        if LLM_PROVIDER == "ollama":
            self._unload_model()

    def _warmup_model(self):
        """Wysyła puste zapytanie do Ollamy z keep_alive=-1, aby załadować model
        do pamięci od razu przy starcie programu, zamiast dopiero przy pierwszym
        rzeczywistym pytaniu użytkownika (co skutkowałoby zauważalną zwłoką)."""
        try:
            response = requests.post(OLLAMA_URL.replace("/v1", "/api/generate"), json={"model": LLM_MODEL, "prompt": "", "keep_alive": -1}, timeout=10)
        except Exception as e:
            logger.warning(f"Nie udało się załadować modelu na starcie: {e}", exc_info=True)

    def _unload_model(self):
        """Wysyła żądanie do Ollamy o natychmiastowe zwolnienie modelu z pamięci
        (keep_alive=0), aby nie zajmował zasobów po zakończeniu programu."""
        try:
            response = requests.post(OLLAMA_URL.replace("/v1", "/api/generate"), json={"model": LLM_MODEL, "keep_alive": 0}, timeout=10)
        except Exception as e:
            logger.warning(f"Nie udało się zwolnić modelu: {e}", exc_info=True)

    def _trim_history(self):
        """Przycina historię rozmowy tak, aby jej przybliżony koszt w tokenach
        (licząc od najnowszej do najstarszej wiadomości) nie przekraczał
        MAX_HISTORY_TOKENS. Wiadomość systemowa (prompt) oraz ostatnia
        wiadomość są zawsze zachowywane. Pary wiadomości 'assistant' (tool call)
        + 'tool' (wynik) są usuwane łącznie, aby nie zostawić historii w niespójnym
        stanie (np. wyniku narzędzia bez odpowiadającego mu wywołania).

        Długość w tokenach jest szacowana bardzo przybliżonie jako liczba znaków
        podzielona przez 4 (approx_tokens) - wystarczająco dokładnie na potrzeby
        pilnowania limitu API, bez konieczności użycia pełnego tokenizera.
        """
        if len(self.history) <= 2:
            return

        system_msg = self.history[0]
        last_msg = self.history[-1]
        middle = self.history[1:-1]

        def approx_tokens(msg):
            # Przybliżona liczba tokenów wiadomości: długość tekstu (w tym
            # ewentualnych wywołań narzędzi) podzielona przez 4 znaki na token.
            content = msg.get("content") or ""
            if not isinstance(content, str):
                content = str(content)
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                content += str(tool_calls)
            return len(content) // 4

        used = approx_tokens(system_msg) + approx_tokens(last_msg)
        budget = MAX_HISTORY_TOKENS - used

        # Przechodzimy od najnowszej wiadomości środkowej do najstarszej,
        # zachowując każdą, dopóki mieści się w pozostałym budżecie tokenów.
        kept_reversed = []
        i = len(middle) - 1
        while i >= 0:
            msg = middle[i]

            # Wiadomość 'tool' zawsze występuje w parze z poprzedzającą ją
            # wiadomością 'assistant' (tool call) - traktujemy je jako nierozdzielny blok.
            if msg.get("role") == "tool" and i - 1 >= 0 and middle[i - 1].get("role") == "assistant":
                pair_cost = approx_tokens(middle[i - 1]) + approx_tokens(msg)
                if budget - pair_cost < 0:
                    break
                budget -= pair_cost
                kept_reversed.append(msg)
                kept_reversed.append(middle[i - 1])
                i -= 2
                continue

            cost = approx_tokens(msg)
            if budget - cost < 0:
                break
            budget -= cost
            kept_reversed.append(msg)
            i -= 1

        kept = list(reversed(kept_reversed))
        self.history = [system_msg] + kept + [last_msg]