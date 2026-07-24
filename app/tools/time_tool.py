from datetime import datetime
from app.logger import get_logger
import logging

logger = get_logger(__name__, level=logging.DEBUG)

def get_current_time() -> str:
    now = datetime.now()

    godzina_num = now.hour
    minuta_num = now.minute
    dzien_tygodnia = now.weekday()

    dni_pl = {
            0: "poniedziałek", 1: "wtorek", 2: "środa",
            3: "czwartek", 4: "piątek", 5: "sobota", 6: "niedziela"
        }
    dzien_pl = dni_pl.get(dzien_tygodnia, dzien_tygodnia)

    godzina = godzina_slownie(godzina_num)
    minuta = minuta_slownie(minuta_num)
    czas_slownie = f"{godzina} {minuta}"
    logger.debug(f"Obecnie jest {godzina} {minuta}, a dzisiaj jest {dzien_pl}.")

    return f"Obecnie jest {czas_slownie}, a dzisiaj jest {dzien_pl}."

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

def godzina_slownie(godzina: int) -> str:

    HOURS_PL = {
        1: "pierwsza",
        2: "druga",
        3: "trzecia",
        4: "czwarta",
        5: "piąta",
        6: "szósta",
        7: "siódma",
        8: "ósma",
        9: "dziewiąta",
        10: "dziesiąta",
        11: "jedenasta",
        12: "dwunasta",
        13: "trzynasta",
        14: "czternasta",
        15: "piętnasta",
        16: "szesnasta",
        17: "siedemnasta",
        18: "osiemnasta",
        19: "dziewiętnasta",
        20: "dwudziesta",
        21: "dwudziesta pierwsza",
        22: "dwudziesta druga",
        23: "dwudziesta trzecia",
    }

    return HOURS_PL.get(godzina, str(godzina))

def minuta_slownie(minuta: int) -> str:
    NUMBERS_PL = {
        0: "zero",
        1: "jeden",
        2: "dwa",
        3: "trzy",
        4: "cztery",
        5: "pięć",
        6: "sześć",
        7: "siedem",
        8: "osiem",
        9: "dziewięć",
        10: "dziesięć",
        11: "jedenaście",
        12: "dwanaście",
        13: "trzynaście",
        14: "czternaście",
        15: "piętnaście",
        16: "szesnaście",
        17: "siedemnaście",
        18: "osiemnaście",
        19: "dziewiętnaście",
        20: "dwadzieścia",
        21: "dwadzieścia jeden",
        22: "dwadzieścia dwa",
        23: "dwadzieścia trzy",
        24: "dwadzieścia cztery",
        25: "dwadzieścia pięć",
        26: "dwadzieścia sześć",
        27: "dwadzieścia siedem",
        28: "dwadzieścia osiem",
        29: "dwadzieścia dziewięć",
        30: "trzydzieści",
        31: "trzydzieści jeden",
        32: "trzydzieści dwa",
        33: "trzydzieści trzy",
        34: "trzydzieści cztery",
        35: "trzydzieści pięć",
        36: "trzydzieści sześć",
        37: "trzydzieści siedem",
        38: "trzydzieści osiem",
        39: "trzydzieści dziewięć",
        40: "czterdzieści",
        41: "czterdzieści jeden",
        42: "czterdzieści dwa",
        43: "czterdzieści trzy",
        44: "czterdzieści cztery",
        45: "czterdzieści pięć",
        46: "czterdzieści sześć",
        47: "czterdzieści siedem",
        48: "czterdzieści osiem",
        49: "czterdzieści dziewięć",
        50: "pięćdziesiąt",
        51: "pięćdziesiąt jeden",
        52: "pięćdziesiąt dwa",
        53: "pięćdziesiąt trzy",
        54: "pięćdziesiąt cztery",
        55: "pięćdziesiąt pięć",
        56: "pięćdziesiąt sześć",
        57: "pięćdziesiąt siedem",
        58: "pięćdziesiąt osiem",
        59: "pięćdziesiąt dziewięć",
    }

    return NUMBERS_PL.get(minuta, str(minuta))