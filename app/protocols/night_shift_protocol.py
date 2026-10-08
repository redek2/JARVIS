import logging
from app.logger import get_logger
from app.tools.lamp_tool import toggle_desk_lamp
from app.tools.power_strip_tool import toggle_socket
from app.tools.bedroom_lights_tool import toggle_main_lights

logger = get_logger(__name__, level=logging.DEBUG)

def night_shift_protocol():
    """Protokół nocnej zmiany, który włącza lampkę biurkową na 30% i ciepłe światło, monitor i gasi główne światło.
    Funkcja jest wywoływana przez LLM jako narzędzie zdefiniowane w NIGHT_SHIFT_PROTOCOL_SCHEMA."""
    logger.info(r"Włączanie protokołu nocnej zmiany: włączanie lampki biurkowej na 30% i ciepłe światło, monitora i wyłączanie głównej lampy.")
    
    lamp_response = toggle_desk_lamp(state="ON", brightness=69, color_temp=500, color="#ffb74a")
    logger.debug(f"Response from toggle_desk_lamp: {lamp_response}")
    
    power_strip_response = toggle_socket(socket_number=4, state="ON")
    logger.debug(f"Response from toggle_power_strip: {power_strip_response}")

    main_lamp_response = toggle_main_lights(state="OFF")
    logger.debug(f"Response from toggle_main_lights: {main_lamp_response}")

    return "Protokół nocnej zmiany został uruchomiony: lampka biurkowa włączona na ciepłą barwę, monitor zasilony, a główne światło zgaszone."

NIGHT_SHIFT_PROTOCOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "night_shift_protocol",
        "description": r"Protokół nocnej zmiany, który włącza lampkę biurkową na 30% i ciepłe światło, monitor i gasi główne światło. Używaj przy poleceniach typu 'włącz tryb nocny', 'protokół nocna zmiana', 'włącz protokół nocnej zmiany'.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}