import json
import logging
import paho.mqtt.publish as publish
from app.logger import get_logger

logger = get_logger(__name__, level=logging.DEBUG)

def toggle_socket(socket_number: int, state: str = None):
    payload = {}
    if socket_number not in [1, 2, 3, 4]:
        logger.warning(f"Nieobsługiwany numer gniazdka: {socket_number}")
        return f"Błąd: Gniazdko o numerze {socket_number} nie istnieje (wybierz 1-4)."

    if not state:
        logger.warning("Nie podano stanu zasilania dla gniazdka.")
        return "Błąd: Należy podać stan (ON, OFF, TOGGLE)."

    payload[f"state_l{socket_number}"] = state.upper()
    
    try:
        publish.single(topic="zigbee2mqtt/0xd885acfffeeb895c/set", payload=json.dumps(payload), hostname="localhost", port=1883)
        logger.debug(f"Published to MQTT: {payload}")
    except Exception as e:
        logger.error(f"Failed to publish to MQTT: {e}")
        return f"Błąd: Nie udało się wysłać polecenia do listwy zasilającej. Szczegóły: {str(e)}"

    return f"Stan gniazdka {socket_number} został zmieniony: {payload}"

POWER_STRIP_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name":"toggle_socket",
        "description": "Steruje zasilaniem gniazdek w inteligentnej listwie/przedłużaczu. Pozwala włączać, wyłączać lub przełączać stan wskazanego gniazdka (od 1 do 4).",
        "parameters": {
            "type": "object",
                "properties": {
                    "socket_number": {
                        "type": "integer",
                        "enum": [1, 2, 3, 4],
                        "description": "Numer gniazdka w listwie zasilającej (od 1 do 4), którym chcesz sterować."
                    },
                    "state": {
                        "type": "string",
                        "enum": ["ON", "OFF", "TOGGLE"],
                        "description": "Docelowy stan zasilania dla wybranego gniazdka: włączenie (ON), wyłączenie (OFF) lub przełączenie stanu na przeciwny (TOGGLE)."
                    }
                },
            "required": ["socket_number", "state"]
        }
    }
}