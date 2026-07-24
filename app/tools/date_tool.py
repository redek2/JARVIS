from datetime import datetime
from app.logger import get_logger
import logging

logger = get_logger(__name__, level=logging.DEBUG)

def get_current_date():
    now = datetime.now()
    day_num = now.day
    month_num = now.month
    year_num = now.year

    day = dzien_slownie(day_num)
    month = miesiac_slownie(month_num)
    year = rok_slownie(year_num)
    date = f"{day} {month} {year}"

    logger.debug(f"Aktualna data to {date} roku")
    return f"Aktualna data to {date} roku"

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

def dzien_slownie(dzien: int) -> str:
    DAYS_PL = {
        1: "pierwszy",
        2: "drugi",
        3: "trzeci",
        4: "czwarty",
        5: "piąty",
        6: "szósty",
        7: "siódmy",
        8: "ósmy",
        9: "dziewiąty",
        10: "dziesiąty",
        11: "jedenasty",
        12: "dwunasty",
        13: "trzynasty",
        14: "czternasty",
        15: "piętnasty",
        16: "szesnasty",
        17: "siedemnasty",
        18: "osiemnasty",
        19: "dziewiętnasty",
        20: "dwudziesty",
        21: "dwudziesty pierwszy",
        22: "dwudziesty drugi",
        23: "dwudziesty trzeci",
        24: "dwudziesty czwarty",
        25: "dwudziesty piąty",
        26: "dwudziesty szósty",
        27: "dwudziesty siódmy",
        28: "dwudziesty ósmy",
        29: "dwudziesty dziewiąty",
        30: "trzydziesty",
        31: "trzydziesty pierwszy"
    }

    return DAYS_PL.get(dzien, str(dzien))

def miesiac_slownie(month: int) -> str:
    MONTHS_PL = {
        1: "stycznia",
        2: "lutego",
        3: "marca",
        4: "kwietnia",
        5: "maja",
        6: "czerwca",
        7: "lipca",
        8: "sierpnia",
        9: "września",
        10: "października",
        11: "listopada",
        12: "grudnia"
    }

    month_slownie = MONTHS_PL.get(month, str(month))
    return f"{month_slownie}"

def rok_slownie(year: int) -> str:
    YEARS_PL = {
        2020: "dwa tysiące dwudziestego",
        2021: "dwa tysiące dwudziestego pierwszego",
        2022: "dwa tysiące dwudziestego drugiego",
        2023: "dwa tysiące dwudziestego trzeciego",
        2024: "dwa tysiące dwudziestego czwartego",
        2025: "dwa tysiące dwudziestego piątego",
        2026: "dwa tysiące dwudziestego szóstego",
        2027: "dwa tysiące dwudziestego siódmego",
        2028: "dwa tysiące dwudziestego ósmego",
        2029: "dwa tysiące dwudziestego dziewiątego",
        2030: "dwa tysiące trzydziestego",
        2031: "dwa tysiące trzydziestego pierwszego",
        2032: "dwa tysiące trzydziestego drugiego",
        2033: "dwa tysiące trzydziestego trzeciego",
        2034: "dwa tysiące trzydziestego czwartego",
        2035: "dwa tysiące trzydziestego piątego",
        2036: "dwa tysiące trzydziestego szóstego",
        2037: "dwa tysiące trzydziestego siódmego",
        2038: "dwa tysiące trzydziestego ósmego",
        2039: "dwa tysiące trzydziestego dziewiątego",
        2040: "dwa tysiące czterdziestego"
    }
    return f"{YEARS_PL.get(year, str(year))}"