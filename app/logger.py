"""
Wspólna konfiguracja logowania dla całej aplikacji JARVIS.

Zapewnia kolorowe (wg poziomu logowania) komunikaty w konsoli oraz
gwarantuje, że każdy moduł wywołujący get_logger() z tą samą nazwą
otrzyma ten sam, raz skonfigurowany obiekt loggera.
"""
import logging
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)  # włącza obsługę kolorów ANSI w konsoli (w tym na Windows)

# Mapowanie poziomu logowania na kolor, którym zostanie wyświetlony komunikat
_COLORS = {
    logging.DEBUG: Fore.BLUE,
    logging.INFO: Fore.CYAN,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.RED + Style.BRIGHT,
}

class ColorFormatter(logging.Formatter):
    """Formatter logów kolorujący cały wiersz zgodnie z poziomem ważności
    komunikatu (DEBUG/INFO/WARNING/ERROR/CRITICAL)."""
    def format(self, record):
        color = _COLORS.get(record.levelno, "")
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Zwraca skonfigurowany logger z kolorowym outputem konsolowym.

    Kolejne wywołania z tą samą nazwą zwracają ten sam logger
    (bez duplikowania handlerów) - bezpieczne przy wielokrotnym imporcie
    i przy użyciu z wielu wątków.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(ColorFormatter("[%(levelname)s][%(name)s] %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False

    return logger