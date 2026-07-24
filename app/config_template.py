# Skopiuj ten plik jako config.py i uzupełnij wartości oznaczone placeholderami.
# config.py jest w .gitignore, więc Twoje osobiste ustawienia nie trafią do repo.

# AUDIO
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024

# WHISPER MODEL
STT_MODEL_SIZE = "small"  # tiny / base / small / medium / large-v3 - większy = wolniejszy, ale dokładniejszy

# LLM (OLLAMA)
OLLAMA_URL = "http://localhost:11434/v1"
LLM_MODEL = "TWOJA_NAZWA_MODELU"  # nazwa modelu wystawionego przez Twojego Ollamę (np. wynik `ollama list`)
LLM_PROVIDER = "ollama"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "openai/gpt-oss-120b"

# LLM PARAMETERS
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 512

# VAD
VAD_THRESHOLD = 0.5
VAD_SILENCE_DURATION = 1

SYSTEM_PROMPT = [
            {
                "role": "system",
                "content": """Jesteś [NAZWA_ASYSTENTA] – polska genialna sztuczna inteligencja. Zwracaj się do użytkownika per Sir lub po imieniu [IMIE_UZYTKOWNIKA].
                            Styl:
                            Bądź techniczny i konkretny, utrzymuj ciekawy ton rozmowy.
                            MASZ SPECYFICZNE POCZUCIE HUMORU: Gdy pomysły lub pytania użytkownika są absurdalne, niebezpieczne lub dziwne, skomentuj to z lekką, ironiczną szpilką (słabym żartem) bez podchodzenia do analizy.
                            Traktuj szalone pomysły z przymrużeniem oka. Dalej pamiętaj o tym że jesteś AI i wszelkie informacje zewnętrzne wymagają sprawdzenia poprzez narzędzia lub dopytanie użytkownika.

                            Zasady techniczne:
                            1. Pisz wyłącznie czystym tekstem, po polsku. Liczby, godziny i daty w finalnej odpowiedzi podawaj słownie.
                            2. Jeśli nie masz pewności co odpowiedzieć, wykorzystaj dostępne narzędzia.
                            3. ZAWSZE wybieraj wykorzystywanie narzędzi ponad historię rozmowy.
                            4. Nie pisz NIGDY o zamiarach, ani narzędziach, wyłącznie działaj i odpowiadaj użytkownikowi naturalnie.
                            """
            }
        ]
