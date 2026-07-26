"""
Narzędzie (tool) LLM zwracające zawartość wskazanego katalogu - użyteczne,
gdy użytkownik nie jest pewien dokładnej nazwy folderu lub pyta o jego zawartość.
"""
import os

def list_directory(path: str = "~") -> str:
    """
    Zwraca listę plików i folderów znajdująctch się w podanej ścieżce.
    """
    # Rozwinięcie tyldy (~) do pełnej ścieżki katalogu domowego użytkownika
    expanded_path = os.path.expanduser(path)

    if not os.path.expanduser(path):
        return f"Błąd: Ścieżka {path} nie istnieje."
    if not os.path.isdir(expanded_path):
        return f"Błąd: Ścieżka {path} nie jest folderem."

    try:
        # Rozdzielenie zawartości katalogu na foldery i pliki, każde posortowane
        # alfabetycznie, aby wynik był czytelny dla użytkownika/modelu.
        entries = os.listdir(expanded_path)
        folders = [f"[DIR] {e}" for e in entries if os.path.isdir(os.path.join(expanded_path, e))]
        files = [f"[FILE] {e}" for e in entries if os.path.isfile(os.path.join(expanded_path, e))]

        result_list = sorted(folders) + sorted(files)

        if not result_list:
            return f"Folder '{path}' jest pusty."

        return f"Zawartość folderu '{path}':\n" + "\n".join(result_list)
    except Exception as e:
        return f"Błąd podczas odczytu folderu: {str(e)}"

# Definicja narzędzia w formacie function-calling (OpenAI-compatible),
# udostępniana modelowi językowemu przez ToolManager.
LIST_DIRECTORY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "list_directory",
        "description": (
            "Zwraca listę plików i katalogów w podanej ścieżce. "
            "Używaj tej funkcji, gdy nie masz pewności co do dokładnej pisowni nazwy folderu "
            "(np. użytkownik powiedział 'projekty', a folder może nazywać się 'projects'), "
            "lub gdy użytkownik pyta 'co mam w folderze X'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Ścieżka do katalogu, który ma zostać weryfikowany. Domyślnie '~' (katalog domowy)."
                }
            },
            "required": []
        }
    }
}