import json
import os
from datetime import datetime
import uuid

class ProgramManager:
    def __init__(self, filename="data/programs.json"):
        self.filename = filename
        self.programs = self.load_programs()
    
    def load_programs(self):
        """Lädt gespeicherte Programme"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {"programs": []}
    
    def save_programs(self):
        """Speichert Programme"""
        try:
            os.makedirs(os.path.dirname(self.filename), exist_ok=True)
            with open(self.filename, 'w') as f:
                json.dump(self.programs, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving programs: {e}")
            return False
    
    def save_program(self, name, positions, program_id=None):
        """Speichert ein neues Programm oder aktualisiert ein bestehendes"""
        if not name or not positions:
            return None
        
        program_data = {
            'id': program_id or str(uuid.uuid4()),
            'name': name,
            'positions': positions,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'steps': len(positions)
        }
        
        if program_id:
            # Update existing program
            for i, prog in enumerate(self.programs['programs']):
                if prog['id'] == program_id:
                    program_data['created'] = prog['created']  # Keep original creation date
                    self.programs['programs'][i] = program_data
                    break
        else:
            # New program
            self.programs['programs'].append(program_data)
        
        self.save_programs()
        return program_data['id']
    
    def get_all_programs(self):
        """Gibt alle Programme zurück"""
        return self.programs.get('programs', [])
    
    def get_program(self, program_id):
        """Gibt ein spezifisches Programm zurück"""
        for program in self.programs.get('programs', []):
            if program['id'] == program_id:
                return program
        return None
    
    def delete_program(self, program_id):
        """Löscht ein Programm"""
        original_count = len(self.programs.get('programs', []))
        self.programs['programs'] = [
            p for p in self.programs.get('programs', [])
            if p['id'] != program_id
        ]
        
        if len(self.programs['programs']) < original_count:
            self.save_programs()
            return True
        return False
    
    def record_position(self, position):
        """Zeichnet eine Position für Programmaufzeichnung auf"""
        return {
            'base': position.get('base', {}).get('set', 90),
            'shoulder': position.get('shoulder', {}).get('set', 90),
            'elbow': position.get('elbow', {}).get('set', 90),
            'wrist': position.get('wrist', {}).get('set', 90),
            'hand': position.get('hand', {}).get('set', 0),
            'timestamp': datetime.now().isoformat()
        }
    
    def create_program_from_recording(self, name, recorded_positions):
        """Erstellt ein Programm aus aufgezeichneten Positionen"""
        # Reduziere redundante Positionen (wenn sich wenig ändert)
        simplified_positions = []
        last_position = None
        
        for pos in recorded_positions:
            if last_position is None or self._position_changed(last_position, pos, threshold=5):
                simplified_positions.append({
                    'base': pos['base'],
                    'shoulder': pos['shoulder'],
                    'elbow': pos['elbow'],
                    'wrist': pos['wrist'],
                    'hand': pos['hand']
                })
                last_position = pos
        
        return self.save_program(name, simplified_positions)
    
    def _position_changed(self, pos1, pos2, threshold=5):
        """Prüft, ob sich die Position signifikant geändert hat"""
        for joint in ['base', 'shoulder', 'elbow', 'wrist', 'hand']:
            if abs(pos1.get(joint, 0) - pos2.get(joint, 0)) > threshold:
                return True
        return False