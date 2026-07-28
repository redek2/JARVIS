"""
Narzędzie (tool) LLM umożliwiające przeszukiwanie prywatnej przestrzeni
użytkownika w Notion (notatki, listy zadań, projekty itp.) za pomocą Notion API.

Przepływ działania:
    1. `_search_notion` - wyszukuje w całym workspace Notion strony/bazy pasujące do frazy.
    2. Dla każdej znalezionej BAZY DANYCH `_query_database` pobiera jej wiersze (rekordy).
    3. `_parse_database_results` + `_extract_property_value` zamieniają surową
       odpowiedź JSON z Notion na czytelny, jednolity tekst dla modelu językowego.

Uwaga: funkcja obsługuje tylko wyniki typu "database" - pojedyncze strony
(nie będące bazami) znalezione w wyszukiwaniu są pomijane.
"""
from app.logger import get_logger
from dotenv import load_dotenv
import os
import logging
import requests

load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
logger = get_logger(__name__, level=logging.DEBUG)

def search_notion_info(query: str = "") -> str:
    """Wyszukuje w Notion treści pasujące do zapytania `query`, a następnie
    dla każdej znalezionej bazy danych pobiera i zwraca jej zawartość jako
    tekst czytelny dla modelu językowego. Funkcja jest wywoływana przez LLM
    jako narzędzie zdefiniowane w NOTION_TOOL_SCHEMA."""
    search_data = _search_notion(query)

    results = search_data.get("results", [])
    if not results:
        return "Nie znaleziono żadnych informacji w Notion"

    output_text = []

    # Interesują nas wyłącznie wyniki będące bazami danych (np. listy zadań,
    # notatki w formie tabeli) - dla każdej pobieramy jej pełną zawartość.
    for item in results:
        if item.get("object") == "database":
            db_id = item.get("id")
            db_data = _query_database(db_id)
            parsed_context = _parse_database_results(db_data)
            output_text.append(parsed_context)

    return "\n".join(output_text) if output_text else "Brak danych w bazach."

def _search_notion(query: str):
    """Wywołuje endpoint wyszukiwania Notion API (`/v1/search`) i zwraca
    surową odpowiedź JSON. W przypadku błędu połączenia loguje go
    i zwraca pusty słownik (bezpieczna wartość domyślna)."""
    url = "https://api.notion.com/v1/search"

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    payload = {"query": query}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching Notion: {e}")
        return {}
    return response.json()

def _query_database(database_id: str):
    """Pobiera wszystkie wiersze (strony) wskazanej bazy danych Notion
    (`/v1/databases/{id}/query`) i zwraca surową odpowiedź JSON.
    W przypadku błędu połączenia loguje go i zwraca pusty słownik."""
    url = f"https://api.notion.com/v1/databases/{database_id}/query"

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    try:
        response = requests.post(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying Notion database: {e}")
        return {}
    return response.json()

def _extract_property_value(prop_data: dict) -> str:
    """Wyciąga czytelną, tekstową wartość pojedynczej właściwości (kolumny)
    rekordu Notion, w zależności od jej typu (title, select, multi_select,
    number, rich_text). Dla nieobsługiwanych typów zwraca pusty ciąg znaków."""
    prop_type = prop_data.get("type")

    if prop_type == "title":
        titles = prop_data.get("title", [])
        return "".join([t.get("plain_text", "") for t in titles])

    elif prop_type == "select":
        select_obj = prop_data.get("select")
        return select_obj.get("name") if select_obj else ""

    elif prop_type == "multi_select":
        items = prop_data.get("multi_select", [])
        return ", ".join([i.get("name", "") for i in items])

    elif prop_type == "number":
        val = prop_data.get("number")
        return str(val) if val is not None else ""

    elif prop_type == "rich_text":
        texts = prop_data.get("rich_text", [])
        return "".join([t.get("plain_text", "") for t in texts])

    return ""

def _parse_database_results(db_results: dict) -> str:
    """Zamienia surową odpowiedź JSON z zapytania do bazy Notion na listę
    czytelnych wierszy tekstowych w formacie "- Kolumna1: wartość | Kolumna2: wartość",
    pomijając puste właściwości. Każda strona (rekord) bazy staje się jednym wierszem."""
    if not db_results or "results" not in db_results:
        return "Brak wyników."

    parsed_rows = []

    for page in db_results["results"]:
        properties = page.get("properties", {})
        row_parts = []

        for prop_name, prop_data in properties.items():
            val = _extract_property_value(prop_data)
            if val:
                row_parts.append(f"{prop_name}: {val}")

        if row_parts:
            parsed_rows.append("- " + " | ".join(row_parts))

    return "\n".join(parsed_rows)


# Definicja narzędzia w formacie function-calling (OpenAI-compatible),
# udostępniana modelowi językowemu przez ToolManager.
NOTION_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_notion_info",
        "description": (
            "Przeszukuje prywatną bazę wiedzy i notatki użytkownika w Notion (nołszyn, nocjon). "
            "Używaj tego narzędzia, gdy użytkownik pyta o swoje osobiste plany, listy zadań (to-do), "
            "zakupy do zrobienia, koszty, projekty programistyczne, notatki lub cokolwiek zapisanego w swoim systemie."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Fraza kluczowa do wyszukiwania w Notion, np. 'zakupy', 'projekty', 'iPhone'. "
                        "Jeśli użytkownik pyta ogólnie o wszystkie notatki, przekaż pusty ciąg znaków ''."
                    )
                }
            },
            "required": ["query"]
        }
    }
}