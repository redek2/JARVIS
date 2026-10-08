import logging
from app.logger import get_logger
from app.tools.lamp_tool import toggle_desk_lamp
from app.tools.power_strip_tool import toggle_socket
from app.tools.bedroom_lights_tool import toggle_main_lights

logger = get_logger(__name__, level=logging.DEBUG)

def sleep_protocol():
    """Protokół snu, który wyłącza lampkę biurkową, monitor i główne światło.
    Funkcja jest wywoływana przez LLM jako narzędzie zdefiniowane w SLEEP_PROTOCOL_SCHEMA."""
    logger.info(r"Włączanie protokołu snu: wyłączanie lampki biurkowej, monitora i głównego światła.")
    
    lamp_response = toggle_desk_lamp(state="OFF")
    logger.debug(f"Response from toggle_desk_lamp: {lamp_response}")
    
    power_strip_response = toggle_socket(socket_number=4, state="OFF")
    logger.debug(f"Response from toggle_power_strip: {power_strip_response}")

    main_lamp_response = toggle_main_lights(state="OFF")
    logger.debug(f"Response from toggle_main_lights: {main_lamp_response}")

    return "Protokół snu został uruchomiony: lampka biurkowa, monitor i główne światło zostały wyłączone."

SLEEP_PROTOCOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "sleep_protocol",
        "description": r"Protokół snu, który wyłącza lampkę biurkową, monitor i główne światło. Używaj przy poleceniach typu 'włącz tryb snu', 'protokół snu', 'włącz protokół snu'.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}