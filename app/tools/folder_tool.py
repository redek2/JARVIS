"""
Narzędzie (tool) LLM pozwalające otworzyć wskazany plik lub folder
w domyślnej aplikacji systemowej (działa na Linuksie za pomocą `xdg-open`).
"""
from app.logger import get_logger
import logging
import os
import subprocess

logger = get_logger(__name__, level=logging.DEBUG)

def open_path(path: str):
    """
    Otwiera folder lub plik w domyślnej aplikacji systemowej.
    Np. path = "~/Pobrane" lub path = "/home/user/Dokumenty"
    """
    # Rozwinięcie tyldy (~) do pełnej ścieżki katalogu domowego użytkownika
    expanded_path = os.path.expanduser(path)

    if os.path.exists(expanded_path):
        # Uruchomienie procesu w tle (Popen) - nie blokuje działania asystenta;
        # `xdg-open` deleguje otwarcie do domyślnej aplikacji związanej z danym typem pliku/folderu.
        subprocess.Popen(["xdg-open", expanded_path],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL
                         )
        return f"Otwarto: {path}"
    else:
        return f"Błąd: Ścieżka {path} nie istnieje."

# Definicja narzędzia w formacie function-calling (OpenAI-compatible),
# udostępniana modelowi językowemu przez ToolManager.
FOLDER_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "open_path",
        "description": "Otwiera podany plik lub folder w domyślnej aplikacji systemowej (np. menedżerze plików, przeglądarce dokumentów czy odtwarzaczu). Używaj tej funkcji, gdy użytkownik prosi o otworzenie, pokazanie lub wyświetlenie konkretnego folderu lub pliku na dysku.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Ścieżka do pliku lub folderu, np. '~/Pobrane', '~/Dokumenty', '/home/user/Obrazy'. Możesz używać tyldy (~) do oznaczania katalogu domowego."
                }
            },
            "required": []
        }
    }
}