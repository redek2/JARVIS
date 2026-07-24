from app.logger import get_logger
from dotenv import load_dotenv
import os
import logging
import requests

load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
logger = get_logger(__name__, level=logging.DEBUG)

def search_notion_info(query: str = "") -> str:
    search_data = _search_notion(query)

    results = search_data.get("results", [])
    if not results:
        return "Nie znaleziono żadnych informacji w Notion"

    output_text = []

    for item in results:
        if item.get("object") == "database":
            db_id = item.get("id")
            db_data = _query_database(db_id)
            parsed_context = _parse_database_results(db_data)
            output_text.append(parsed_context)

    return "\n".join(output_text) if output_text else "Brak danych w bazach."

def _search_notion(query: str):
    url = "https://api.notion.com/v1/search"

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    payload = {"query": query}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching Notion: {e}")
        return {}
    return response.json()

def _query_database(database_id: str):
    url = f"https://api.notion.com/v1/databases/{database_id}/query"

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying Notion database: {e}")
        return {}
    return response.json()

def _extract_property_value(prop_data: dict) -> str:
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