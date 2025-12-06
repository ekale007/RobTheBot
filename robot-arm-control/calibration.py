import json
import os

class CalibrationManager:
    def __init__(self, filename="data/calibration.json"):
        self.filename = filename
        self.calibration_data = self.load_calibration()
        
        # Standardkalibrierung falls Datei nicht existiert
        if not self.calibration_data:
            self.calibration_data = {
                'joints': {
                    'base': {'min': 0, 'max': 180, 'home': 90},
                    'shoulder': {'min': 0, 'max': 180, 'home': 90},
                    'elbow': {'min': 0, 'max': 180, 'home': 90},
                    'wrist': {'min': 0, 'max': 180, 'home': 90},
                    'hand': {'min': 0, 'max': 90, 'home': 0}
                },
                'last_calibrated': None,
                'calibration_points': {}
            }
    
    def load_calibration(self):
        """Lädt Kalibrierungsdaten aus Datei"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    return json.load(f)
        except:
            pass
        return None
    
    def save_calibration(self):
        """Speichert Kalibrierungsdaten"""
        try:
            os.makedirs(os.path.dirname(self.filename), exist_ok=True)
            with open(self.filename, 'w') as f:
                json.dump(self.calibration_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving calibration: {e}")
            return False
    
    def calibrate_joint(self, joint, cal_type, value):
        """Führt eine Kalibrierung für ein Gelenk durch"""
        if joint not in self.calibration_data['joints']:
            return {'success': False, 'error': 'Invalid joint'}
        
        if cal_type not in ['min', 'max', 'home']:
            return {'success': False, 'error': 'Invalid calibration type'}
        
        try:
            value = int(value)
            
            if cal_type == 'min':
                # Min-Wert darf nicht größer als aktueller Max-Wert sein
                current_max = self.calibration_data['joints'][joint]['max']
                if value >= current_max:
                    return {'success': False, 'error': 'Min must be less than max'}
                self.calibration_data['joints'][joint]['min'] = value
                
            elif cal_type == 'max':
                # Max-Wert darf nicht kleiner als aktueller Min-Wert sein
                current_min = self.calibration_data['joints'][joint]['min']
                if value <= current_min:
                    return {'success': False, 'error': 'Max must be greater than min'}
                self.calibration_data['joints'][joint]['max'] = value
                
            elif cal_type == 'home':
                # Home muss zwischen min und max liegen
                current_min = self.calibration_data['joints'][joint]['min']
                current_max = self.calibration_data['joints'][joint]['max']
                if not (current_min <= value <= current_max):
                    return {'success': False, 'error': 'Home must be between min and max'}
                self.calibration_data['joints'][joint]['home'] = value
            
            # Speichere Kalibrierungspunkt
            from datetime import datetime
            if 'calibration_points' not in self.calibration_data:
                self.calibration_data['calibration_points'] = {}
            
            point_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.calibration_data['calibration_points'][point_id] = {
                'joint': joint,
                'type': cal_type,
                'value': value,
                'timestamp': datetime.now().isoformat()
            }
            
            self.calibration_data['last_calibrated'] = datetime.now().isoformat()
            
            return {
                'success': True,
                'joint': joint,
                'type': cal_type,
                'value': value,
                'min': self.calibration_data['joints'][joint]['min'],
                'max': self.calibration_data['joints'][joint]['max'],
                'home': self.calibration_data['joints'][joint]['home']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_calibration_data(self):
        """Gibt alle Kalibrierungsdaten zurück"""
        return self.calibration_data
    
    def get_joint_limits(self, joint):
        """Gibt die Grenzen für ein Gelenk zurück"""
        if joint in self.calibration_data['joints']:
            return self.calibration_data['joints'][joint]
        return None
    
    def reset_calibration(self, joint=None):
        """Setzt Kalibrierung zurück (alle oder für ein Gelenk)"""
        if joint:
            if joint in self.calibration_data['joints']:
                # Auf Standard zurücksetzen
                defaults = {
                    'base': {'min': 0, 'max': 180, 'home': 90},
                    'shoulder': {'min': 0, 'max': 180, 'home': 90},
                    'elbow': {'min': 0, 'max': 180, 'home': 90},
                    'wrist': {'min': 0, 'max': 180, 'home': 90},
                    'hand': {'min': 0, 'max': 90, 'home': 0}
                }
                self.calibration_data['joints'][joint] = defaults[joint]
        else:
            # Alle zurücksetzen
            self.calibration_data = {
                'joints': {
                    'base': {'min': 0, 'max': 180, 'home': 90},
                    'shoulder': {'min': 0, 'max': 180, 'home': 90},
                    'elbow': {'min': 0, 'max': 180, 'home': 90},
                    'wrist': {'min': 0, 'max': 180, 'home': 90},
                    'hand': {'min': 0, 'max': 90, 'home': 0}
                },
                'last_calibrated': None,
                'calibration_points': {}
            }
        
        return self.save_calibration()