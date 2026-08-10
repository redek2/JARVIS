import json
import logging
import paho.mqtt.publish as publish
from app.logger import get_logger

logger = get_logger(__name__, level=logging.DEBUG)

def toggle_light(state: str = None, brightness: int = None, color_temp: int = None, color: str = None):
    payload = {}
    if state is not None:
        payload["state"] = state.upper()
    if brightness is not None:
        payload["brightness"] = int((brightness / 100) * 254)
    if color_temp is not None:
        payload["color_temp"] = color_temp
    if color is not None:
        payload["color"] = {"hex": color}

    if not payload:
        logger.warning("Nie podano żadnych parametrów do zmiany stanu światła.")
        return "Błąd: Nie podano żadnych parametrów do zmiany stanu światła."

    try:
        publish.single(topic="zigbee2mqtt/0x006ce4a4ffce0078/set", payload=json.dumps(payload), hostname="localhost", port=1883)
        logger.debug(f"Published to MQTT: {payload}")
    except Exception as e:
        logger.error(f"Failed to publish to MQTT: {e}")
        return f"Błąd: Nie udało się wysłać polecenia do żarówki. Szczegóły: {str(e)}"

    return f"Ustawienia żarówki zostały zmienione: {payload}"

LIGHT_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "toggle_light",
        "description": "Steruje żarówką w sypialni/pokoju: włącza/wyłącza ją, zmienia jasność oraz temperaturę barwową. Zmiana koloru światła w formacie HEX (np. #FF5733) jest również możliwa.",
        "parameters": {
            "type": "object",
                "properties": {
                    "state": {
                        "type": ["string", "null"],
                        "enum": ["ON", "OFF", "TOGGLE"],
                        "description": "Stan zasilania żarówki."
                    },
                    "brightness": {
                        "type": ["integer", "null"],
                        "description": "Jasność światła wyrażona w procentach od 0 do 100."
                    },
                    "color_temp": {
                        "type": ["integer", "null"],
                        "description": "Temperatura barwowa w miredach: od 153 (bardzo zimne białe światło) do 555 (bardzo ciepłe/żółte światło)."
                    },
                    "color": {
                        "type": ["string", "null"],
                        "description": "Kolor światła w formacie HEX (np. '#FF0000' dla czerwonego, '#00FF00' dla zielonego)."
                    }
                },
            "required": []
        }
    }
}