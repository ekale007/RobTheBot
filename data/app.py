#!/usr/bin/env python3
"""
Hauptanwendung für Roboterarm-Steuerung
Kommunikation mit ESP8266 über HTTP/MQTT
"""

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO
import json
import time
import threading
from datetime import datetime
import logging

# Eigene Module
from arm_controller import RobotArmController
from calibration import CalibrationManager
from programs import ProgramManager

# Flask App initialisieren
app = Flask(__name__)
app.secret_key = 'robot-arm-secret-key-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Globale Instanzen
arm_controller = RobotArmController()
calibration_manager = CalibrationManager()
program_manager = ProgramManager()

# Aktuelle Arm-Position
current_position = {
    'base': {'set': 125, 'actual': 135, 'min': 0, 'max': 180},
    'shoulder': {'set': 90, 'actual': 90, 'min': 0, 'max': 180},
    'elbow': {'set': 15, 'actual': 45, 'min': 0, 'max': 180},
    'wrist': {'set': 135, 'actual': 195, 'min': 0, 'max': 180},
    'hand': {'set': 10, 'actual': 10, 'min': 0, 'max': 90},
    'led': False
}

# Programmlaufstatus
running_program = None
program_thread = None

@app.route('/')
def index():
    """Hauptsteuerungsseite"""
    return render_template('index.html', 
                         position=current_position,
                         connected=arm_controller.connected)

@app.route('/simulation')
def simulation():
    """Simulationsansicht"""
    return render_template('simulation.html')

@app.route('/calibration')
def calibration_page():
    """Kalibrierungsseite"""
    cal_data = calibration_manager.get_calibration_data()
    return render_template('calibration.html', calibration=cal_data)

@app.route('/programs')
def programs_page():
    """Programmverwaltung"""
    programs = program_manager.get_all_programs()
    return render_template('programs.html', programs=programs)

# API Endpoints für Arm-Steuerung
@app.route('/api/control', methods=['POST'])
def control_arm():
    """Einzelnes Gelenk steuern"""
    try:
        data = request.get_json()
        joint = data.get('joint')
        value = int(data.get('value'))
        
        if joint not in current_position:
            return jsonify({'error': 'Invalid joint'}), 400
            
        # Grenzen prüfen
        min_val = current_position[joint]['min']
        max_val = current_position[joint]['max']
        
        if value < min_val or value > max_val:
            return jsonify({'error': f'Value out of range ({min_val}-{max_val})'}), 400
        
        # An ESP8266 senden
        success = arm_controller.move_joint(joint, value)
        
        if success:
            current_position[joint]['set'] = value
            # Aktualisiere alle Clients über WebSocket
            socketio.emit('position_update', {
                'joint': joint,
                'set': value,
                'timestamp': datetime.now().isoformat()
            })
            return jsonify({'success': True, 'set': value})
        else:
            return jsonify({'error': 'ESP8266 communication failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/position', methods=['POST'])
def set_position():
    """Komplette Position setzen"""
    try:
        data = request.get_json()
        position = data.get('position', {})
        
        for joint, value in position.items():
            if joint in current_position:
                success = arm_controller.move_joint(joint, int(value))
                if success:
                    current_position[joint]['set'] = int(value)
        
        socketio.emit('full_position_update', current_position)
        return jsonify({'success': True, 'position': current_position})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/read_position', methods=['GET'])
def read_position():
    """Aktuelle Position vom ESP8266 lesen"""
    try:
        # Hier würde die Kommunikation mit ESP8266 stattfinden
        # Für jetzt simulieren wir es
        for joint in current_position:
            if joint != 'led':
                # Simuliere kleine Abweichung
                deviation = arm_controller.get_position_from_esp(joint)
                current_position[joint]['actual'] = deviation
        
        return jsonify({'success': True, 'position': current_position})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/led', methods=['POST'])
def control_led():
    """Onboard LED steuern"""
    try:
        data = request.get_json()
        state = data.get('state', False)
        
        success = arm_controller.set_led(state)
        if success:
            current_position['led'] = state
            socketio.emit('led_update', {'state': state})
            return jsonify({'success': True, 'state': state})
        else:
            return jsonify({'error': 'LED control failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Kalibrierungs-API
@app.route('/api/calibrate', methods=['POST'])
def calibrate():
    """Kalibrierung durchführen"""
    try:
        data = request.get_json()
        joint = data.get('joint')
        type = data.get('type')  # 'min', 'max', or 'home'
        value = data.get('value', 0)
        
        result = calibration_manager.calibrate_joint(joint, type, value)
        
        if result['success']:
            # Grenzen aktualisieren
            if 'min' in result:
                current_position[joint]['min'] = result['min']
            if 'max' in result:
                current_position[joint]['max'] = result['max']
            
            socketio.emit('calibration_update', result)
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calibration/save', methods=['POST'])
def save_calibration():
    """Kalibrierung speichern"""
    try:
        success = calibration_manager.save_calibration()
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Programm-API
@app.route('/api/program/save', methods=['POST'])
def save_program():
    """Programm speichern"""
    try:
        data = request.get_json()
        name = data.get('name')
        positions = data.get('positions', [])
        
        if not name or not positions:
            return jsonify({'error': 'Name and positions required'}), 400
            
        program_id = program_manager.save_program(name, positions)
        return jsonify({'success': True, 'id': program_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/program/run', methods=['POST'])
def run_program():
    """Programm ausführen"""
    global running_program, program_thread
    
    try:
        data = request.get_json()
        program_id = data.get('program_id')
        speed = data.get('speed', 1.0)  # 0.5 = langsam, 2.0 = schnell
        
        program = program_manager.get_program(program_id)
        if not program:
            return jsonify({'error': 'Program not found'}), 404
        
        # Stoppe laufendes Programm
        if running_program:
            stop_program()
        
        # Starte Programm in eigenem Thread
        running_program = program_id
        program_thread = threading.Thread(
            target=execute_program,
            args=(program, speed)
        )
        program_thread.daemon = True
        program_thread.start()
        
        socketio.emit('program_started', {
            'program_id': program_id,
            'name': program['name']
        })
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def execute_program(program, speed):
    """Programm ausführen (im Hintergrund-Thread)"""
    positions = program['positions']
    delay = 1.0 / speed  # Anpassung der Geschwindigkeit
    
    for i, position in enumerate(positions):
        if running_program != program['id']:
            break  # Programm wurde gestoppt
            
        # Position setzen
        for joint, value in position.items():
            if joint in current_position:
                arm_controller.move_joint(joint, value)
                current_position[joint]['set'] = value
        
        # Fortschritt senden
        socketio.emit('program_progress', {
            'step': i + 1,
            'total': len(positions),
            'percentage': int((i + 1) / len(positions) * 100)
        })
        
        time.sleep(delay)
    
    # Programm beendet
    socketio.emit('program_finished', {'program_id': program['id']})
    global running_program
    running_program = None

@app.route('/api/program/stop', methods=['POST'])
def stop_program():
    """Aktuelles Programm stoppen"""
    global running_program
    running_program = None
    
    socketio.emit('program_stopped', {})
    return jsonify({'success': True})

@app.route('/api/program/delete', methods=['POST'])
def delete_program():
    """Programm löschen"""
    try:
        data = request.get_json()
        program_id = data.get('program_id')
        
        success = program_manager.delete_program(program_id)
        return jsonify({'success': success})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Client verbunden"""
    print(f"Client connected: {request.sid}")
    socketio.emit('initial_data', {
        'position': current_position,
        'connected': arm_controller.connected
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Client getrennt"""
    print(f"Client disconnected: {request.sid}")

if __name__ == '__main__':
    print("=== Robot Arm Control System ===")
    print("Starting server on http://0.0.0.0:5000")
    print("Press Ctrl+C to stop")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)