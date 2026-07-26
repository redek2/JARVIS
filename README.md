# JARVIS Assistant

JARVIS Assistant to hobbystyczny projekt, którego celem jest zbudowanie od podstaw prywatnego asystenta głosowego, który potrafi korzystać z dowolnych narzędzi wraz z integracją z Home Assistant.

Projekt nie jest produktem ani gotowym rozwiązaniem "plug and play" — to żywy, rozwijany krok po kroku system, budowany dla przyjemności i nauki.

## Jak to działa

Rozmowa z JARVISEM przebiega w prostej, powtarzalnej pętli:

1. **Nagrywanie** — mikrofon nasłuchuje w tle, a wbudowany detektor aktywności głosowej (VAD) sam wykrywa początek i koniec Twojej wypowiedzi (nie trzeba niczego naciskać).
2. **Transkrypcja (STT)** — nagranie jest zamieniane na tekst lokalnie, przy użyciu modelu Whisper (`faster-whisper`).
3. **Rozumowanie (LLM)** — tekst trafia do modelu językowego, który odpowiada strumieniowo i — jeśli trzeba — sam decyduje się skorzystać z dostępnych narzędzi (np. sprawdzić godzinę, przeszukać notatki w Notion, otworzyć folder).
4. **Odpowiedź (TTS)** — wygenerowana odpowiedź jest czytana na głos lokalnym, polskim modelem głosowym, zdanie po zdaniu — równolegle do dalszego generowania tekstu przez model, żeby odpowiedź była płynna i szybka.

Rozmowa kończy się automatycznie po dłuższej ciszy albo gdy powiesz jedną z fraz pożegnalnych ("żegnaj", "adios", "dobranoc"...).

## Funkcje

- **Naturalna rozmowa głosowa po polsku** — pełny cykl głos → tekst → myślenie → głos, bez potrzeby wpisywania czegokolwiek.
- **Automatyczne wykrywanie mowy (VAD)** — asystent sam wie, kiedy zacząłeś i skończyłeś mówić.
- **Wywoływanie narzędzi (function calling)** — model samodzielnie decyduje, kiedy sięgnąć po narzędzie zamiast zgadywać:
  - podanie aktualnej daty i godziny (wypowiadanych słownie),
  - przeszukiwanie prywatnej bazy wiedzy w **Notion** (notatki, listy zadań, projekty),
  - otwieranie plików i folderów w domyślnej aplikacji systemowej,
  - listowanie zawartości katalogów.
- **Elastyczny dostawca LLM** — obecnie projekt przewiduje wykorzstanie **Ollama** (lokalnie) lub **Groq** (chmura, wymagany klucz API)
- **Architektura wielowątkowa** — nagrywanie, generowanie odpowiedzi i synteza mowy działają równolegle, dzięki czemu JARVIS zaczyna mówić, zanim jeszcze skończy "myśleć".
- **Zarządzanie historią rozmowy** — automatyczne przycinanie historii do budżetu tokenów, tak by długie rozmowy nie wysypywały limitów API.

## Struktura projektu

```
jarvis-assistant/
├── main.py                  # Punkt wejścia, główna pętla konwersacji
├── requirements.txt
├── app/
│   ├── config.py             # Aktywna konfiguracja (poza repozytorium)
│   ├── config_template.py    # Szablon konfiguracji
│   ├── audio_recorder.py     # Nagrywanie + wykrywanie aktywności głosowej (VAD)
│   ├── logger.py             # Wspólne, kolorowe logowanie
│   ├── stt/
│   │   └── stt_engine.py     # Rozpoznawanie mowy (faster-whisper)
│   ├── llm/
│   │   └── llm_engine.py     # Komunikacja z LLM, historia rozmowy, tool calling
│   ├── tts/
│   │   └── tts_engine.py     # Synteza mowy (sherpa-onnx / VITS Piper)
│   └── tools/                # Narzędzia (function calling) dostępne dla LLM
│       ├── tool_manager.py
│       ├── date_tool.py
│       ├── time_tool.py
│       ├── folder_tool.py
│       ├── list_dir_tool.py
│       └── notion_tool.py
└── voices/                   # Model głosowy TTS (offline, j. polski)
```

## Znane problemy

- Projekt był dotąd rozwijany i testowany na Linuksie — przynajmniej jeden znany problem uniemożliwia obecnie poprawne działanie na Windowsie. Wsparcie dla Windows jest w planach.
- Modele klasy 8B mają problemy w korzystaniu z narzędzi na zadowalającym poziomie i często halucynują ich użycie, stąd obecnie używany jest Groq