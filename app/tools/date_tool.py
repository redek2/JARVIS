from datetime import datetime

def get_current_date():
    now = datetime.now()
    date = now.strftime("%d.%B.%Y")

    #print(f"[DEBUG] Aktualna data to {date}")
    return f"Aktualna data to {date}"

DATE_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_current_date",
        "description": "Zwracana jest AKTUALNA data, dzień, miesiąc i rok. Używaj tego narzędzia za KAŻDYM razem gdy użytkownik pyta o datę, miesiąc, rok. Nie polegaj na innych danych daty, miesiąca ani roku poza tym narzędziem, używaj tylko aktualnej daty z narzędzia.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}