import requests
import time
import json
from threading import Lock

class RobotArmController:
    def __init__(self, esp_ip="192.168.4.1"):
        self.esp_ip = esp_ip
        self.base_url = f"http://{esp_ip}"
        self.connected = False
        self.lock = Lock()
        self.timeout = 2.0
        
        # Test connection
        self.test_connection()
    
    def test_connection(self):
        """Testet die Verbindung zum ESP8266"""
        try:
            response = requests.get(f"{self.base_url}/status", timeout=self.timeout)
            self.connected = response.status_code == 200
            print(f"ESP8266 connection: {'OK' if self.connected else 'FAILED'}")
        except:
            self.connected = False
            print("ESP8266 connection: FAILED - Check IP address and connection")
    
    def move_joint(self, joint, angle):
        """Bewegt ein Gelenk zum angegebenen Winkel"""
        with self.lock:
            try:
                # Mapping der Gelenknamen zu ESP8266-Pins/Endpoints
                joint_map = {
                    'base': 'servo1',
                    'shoulder': 'servo2',
                    'elbow': 'servo3',
                    'wrist': 'servo4',
                    'hand': 'servo5'
                }
                
                if joint not in joint_map:
                    return False
                
                # Sende Befehl an ESP8266
                url = f"{self.base_url}/control"
                data = {
                    'servo': joint_map[joint],
                    'angle': angle
                }
                
                response = requests.post(url, json=data, timeout=self.timeout)
                
                if response.status_code == 200:
                    print(f"Joint {joint} moved to {angle}°")
                    return True
                else:
                    print(f"Failed to move joint {joint}: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"Error moving joint {joint}: {e}")
                self.connected = False
                return False
    
    def set_led(self, state):
        """Steuert die Onboard-LED"""
        with self.lock:
            try:
                url = f"{self.base_url}/led"
                data = {'state': 1 if state else 0}
                response = requests.post(url, json=data, timeout=self.timeout)
                return response.status_code == 200
            except:
                return False
    
    def get_position_from_esp(self, joint):
        """Liest die aktuelle Position vom ESP8266 (simuliert)"""
        # In der realen Implementierung würde dies vom ESP gelesen
        # Für jetzt: Simuliere eine Position basierend auf Set-Wert + Zufallsabweichung
        import random
        return random.randint(-2, 2)  # Simulierte Abweichung
    
    def emergency_stop(self):
        """Not-Aus: Stoppt alle Bewegungen"""
        try:
            url = f"{self.base_url}/emergency"
            response = requests.post(url, timeout=1.0)
            return response.status_code == 200
        except:
            return False