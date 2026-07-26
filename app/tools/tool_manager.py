"""
Centralny rejestr narzędzi (tools) dostępnych dla modelu językowego JARVISA.

Aby dodać nowe narzędzie do systemu, należy:
    1. Zaimplementować funkcję obsługującą i jej schemat function-calling w app/tools/.
    2. Dodać wpis w `_tools_map` (nazwa -> funkcja) oraz schemat w liście `schemas`.
LLMEngine korzysta z `ToolManager.schemas`, aby poinformować model o dostępnych
narzędziach, a następnie z `execute_tool`, aby faktycznie je wywołać.
"""
from app.tools.time_tool import get_current_time, TIME_TOOL_SCHEMA
from app.tools.date_tool import get_current_date, DATE_TOOL_SCHEMA
from app.tools.notion_tool import search_notion_info, NOTION_TOOL_SCHEMA
from app.tools.folder_tool import open_path, FOLDER_TOOL_SCHEMA
from app.tools.list_dir_tool import list_directory, LIST_DIRECTORY_SCHEMA
from app.logger import get_logger
import logging

logger = get_logger(__name__, level=logging.ERROR)

class ToolManager:
    """Rejestruje dostępne narzędzia (nazwa -> funkcja Pythona) wraz z ich
    schematami function-calling i udostępnia bezpieczne wywoływanie ich
    na podstawie nazwy i argumentów otrzymanych od modelu językowego."""
    def __init__(self):
        # Mapowanie nazwy narzędzia (zgodnej z polem "name" w schemacie)
        # na rzeczywistą funkcję Pythona, która ma zostać wykonana.
        self._tools_map = {
            "get_current_time": get_current_time,
            "get_current_date": get_current_date,
            "search_notion_info": search_notion_info,
            "open_path": open_path,
            "list_directory": list_directory
        }

        # Lista schematów (opisów) narzędzi w formacie OpenAI function-calling,
        # przekazywana do modelu językowego przy każdym zapytaniu.
        self.schemas = [
            TIME_TOOL_SCHEMA,
            DATE_TOOL_SCHEMA,
            NOTION_TOOL_SCHEMA,
            FOLDER_TOOL_SCHEMA,
            LIST_DIRECTORY_SCHEMA
        ]

    def execute_tool(self, name: str, arguments: dict) -> str:
        """Wykonuje narzędzie o podanej nazwie z przekazanymi argumentami
        (rozpakowanymi jako **kwargs). Jeśli narzędzie o danej nazwie nie
        istnieje lub jego wykonanie zakończy się wyjątkiem, zwraca czytelny
        komunikat błędu zamiast rzucać wyjątek dalej - dzięki temu błąd
        narzędzia nie przerywa całej rozmowy z użytkownikiem."""
        tool_func = self._tools_map.get(name)

        if not tool_func:
            return f"Błąd: Narzędzie o nazwie '{name}' nie istnieje w systemie JARVIS"
        
        try:
            result = tool_func(**arguments)
            return result
        except Exception as e:
            logger.error(f"Błąd wykonania narzędzia {name}: {e}", exc_info=True)
            return f"Błąd podczas wykonywania narzędzia {name}: {str(e)}"