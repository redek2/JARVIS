from app.tools.time_tool import get_current_time, TIME_TOOL_SCHEMA
from app.tools.date_tool import get_current_date, DATE_TOOL_SCHEMA

class ToolManager:
    def __init__(self):
        self._tools_map = {
            "get_current_time": get_current_time,
            "get_current_date": get_current_date,
        }

        self.schemas = [
            TIME_TOOL_SCHEMA,
            DATE_TOOL_SCHEMA,
        ]

    def execute_tool(self, name: str, arguments: dict) -> str:
        tool_func = self._tools_map.get(name)

        if not tool_func:
            return f"Błąd: Narzędzie o nazwie '{name}' nie istnieje w systemie JARVIS"
        
        try:
            result = tool_func(**arguments)
            return result
        except Exception as e:
            return f"Błąd podczas wykonywania narzędzia {name}: {str(e)}"