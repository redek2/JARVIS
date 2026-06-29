from datetime import datetime

def get_current_time() -> str:
    now = datetime.now()

    godzina = now.strftime("%H:%M")
    dzien_tygodnia = now.strftime("%A")
    dni_pl = {
            "Monday": "poniedziałek", "Tuesday": "wtorek", "Wednesday": "środa",
            "Thursday": "czwartek", "Friday": "piątek", "Saturday": "sobota", "Sunday": "niedziela"
        }
    dzien_pl = dni_pl.get(dzien_tygodnia, dzien_tygodnia)

    #print(f"\n[DEBUG] Python faktycznie odpalił funkcję! Czas z systemu: {godzina}")

    return f"Aktualny czas systemowy to godzina {godzina}, a dzisiejszy dzień to {dzien_pl}"

TIME_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "Zwraca AKTUALNĄ godzinę oraz dzień tygodnia. Używaj tego narzędzia za KAŻDYM razem gdy użytkownik pyta o czas lub dzień tygodnia. Nie polegaj na innych danych czasu ani dnia tygodnia poza tym narzędziem.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}