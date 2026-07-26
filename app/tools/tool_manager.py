from app.tools.time_tool import get_current_time, TIME_TOOL_SCHEMA
from app.tools.date_tool import get_current_date, DATE_TOOL_SCHEMA
from app.tools.notion_tool import search_notion_info, NOTION_TOOL_SCHEMA
from app.tools.folder_tool import open_path, FOLDER_TOOL_SCHEMA
from app.tools.list_dir_tool import list_directory, LIST_DIRECTORY_SCHEMA
from app.logger import get_logger
import logging

logger = get_logger(__name__, level=logging.ERROR)

class ToolManager:
    def __init__(self):
        self._tools_map = {
            "get_current_time": get_current_time,
            "get_current_date": get_current_date,
            "search_notion_info": search_notion_info,
            "open_path": open_path,
            "list_directory": list_directory
        }

        self.schemas = [
            TIME_TOOL_SCHEMA,
            DATE_TOOL_SCHEMA,
            NOTION_TOOL_SCHEMA,
            FOLDER_TOOL_SCHEMA,
            LIST_DIRECTORY_SCHEMA
        ]

    def execute_tool(self, name: str, arguments: dict) -> str:
        tool_func = self._tools_map.get(name)

        if not tool_func:
            return f"Błąd: Narzędzie o nazwie '{name}' nie istnieje w systemie JARVIS"
        
        try:
            result = tool_func(**arguments)
            return result
        except Exception as e:
            logger.error(f"Błąd wykonania narzędzia {name}: {e}", exc_info=True)
            return f"Błąd podczas wykonywania narzędzia {name}: {str(e)}"