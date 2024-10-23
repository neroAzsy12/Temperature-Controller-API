from quart import Blueprint, jsonify, request
from utils.helpers import (
    celsius_to_fahrenheit,
    create_instrument,
    get_current_timestamp
)
from utils.validators import (
    validate_device_id
)

""" List of available registers """

""" Probe Configuration Registers """
T1_AIR_PROBE_TEMPERATURE_REGISTER = 0           # Read Only, Register for reading temperature from T1
T2_EVAPORATOR_PROBE_TEMPERATURE_REGISTER = 1    # Read Only, Register for reading temperature from T2
T2_ENABLED_REGISTER = 705                       # Read/Write, Register for enabling/disabling T2 probe, as well as checking the status

""" Status Registers for checking status of Compressor, Evap, Defrost """
COMPRESSOR_OUTPUT_REGISTER = 137        # Read Only, 1 = Compressor is currently on, 0 = Compressor is currently off 
EVAPORATOR_FAN_OUTPUT_REGISTER = 138    # Read Only, 1 = Compressor is currently on, 0 = Compressor is currently off
DEFROST_OUTPUT_REGISTRER = 139          # Read Only, 1 = Compressor is currently on, 0 = Compressor is currently off
AUXILLARY_OUTPUT_1_REGISTER = 140       # Read Only, 1 = Door Heater is currently on, 0 = Door Heater is currently off

""" Standby Mode Register """
STANDBY_REGISTER = 701

""" Lights Registers """
LIGHTS_REGISTER = 707

""" SPL, SP, and SPH Registers """
SETPOINT_LOW_REGISTER = 201
SETPOINT_REGISTER = 203
SETPOINT_HIGH_REGISTER = 202

""" HY0 and HY1 Differential Registers """
HY0_REGISTER = 204
HY1_REGISTER = 205

""" Defrost Start Mode Registers """
DEFROST_START_MODE_REGISTER = 209
DEFROST_START_MODE_MAP = {
    0: "NON",
    1: "TIM",
    2: "FRO",
    3: "RTC"
}

DEFROST_TYPE_REIGSTER = 213
DEFROST_TYPE_MAP = {
    0: "OFF",
    1: "ELE",
    2: "GAS"
}

cabinet_blueprint = Blueprint('cabinet', __name__)
rs485_device_collection = None
rs485_device_settings_collection = None

def init_app(app, db):
    global rs485_device_collection
    global rs485_device_settings_collection
    rs485_device_collection = db['rs485_devices']
    rs485_device_settings_collection = db['rs485_device_controller_settings']

@cabinet_blueprint.route('/cabinet/status', methods = ["GET"])
async def get_cabinet_status(device_id):
    """
    Gets the status of cold cabinet

    This endpoint retrieves the current status of the cold cabinet,
        - T1 Probe Temperature (Celsius or Fahrenheit)
        - T2 Probe Temperature (Celsius or Fahrenheit)
        - Current status of compressor (on/off)
        - Current status of evaporator fan (on/off)
        - Current status of defrost (on/off)

    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Query Parameters:
        unit (str): Optional. Specify the temperature unit
            - 'C' for Celsius (default)
            - 'F' for Fahrenheit
    
    Returns:
        JSON response with the current cold cabinet status, and a timestamp
    """
    validate_device_id(device_id, rs485_device_collection)

    unit = request.args.get('unit', default='C', type=str).upper()
    
    if unit not in ['C', 'F']:
        return jsonify({"error": "Invalid unit specified. Use 'C' for Celsius or 'F' for Fahrenheit."}), 400
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        # Setpoints
        setpoint_low = instrument.read_register(registeraddress=SETPOINT_LOW_REGISTER, number_of_decimals=1, functioncode=3, signed=True)
        setpoint_high = instrument.read_register(registeraddress=SETPOINT_HIGH_REGISTER, number_of_decimals=1, functioncode=3, signed=True)
        setpoint = instrument.read_register(registeraddress=SETPOINT_REGISTER, number_of_decimals=1, functioncode=3, signed=True)
        
        # Differentials
        hy0 = instrument.read_register(registeraddress=HY0_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        hy1 = instrument.read_register(registeraddress=HY1_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        standby_mode_status = instrument.read_register(registeraddress=STANDBY_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        t1_temperature = instrument.read_register(registeraddress=T1_AIR_PROBE_TEMPERATURE_REGISTER, number_of_decimals=1, functioncode=3, signed=True)
        t2_temperature = instrument.read_register(registeraddress=T2_EVAPORATOR_PROBE_TEMPERATURE_REGISTER, number_of_decimals=1, functioncode=3, signed=True)
        evaporator_fan_status = instrument.read_register(registeraddress=EVAPORATOR_FAN_OUTPUT_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        compressor_status = instrument.read_register(registeraddress=COMPRESSOR_OUTPUT_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        door_heater_status = instrument.read_register(registeraddress=AUXILLARY_OUTPUT_1_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        cabinet_lights_status = instrument.read_register(registeraddress=LIGHTS_REGISTER, number_of_decimals=0, functioncode=3, signed=False)

        # Defrost related functions
        defrost_status = instrument.read_register(registeraddress=DEFROST_OUTPUT_REGISTRER, number_of_decimals=0, functioncode=3, signed=False)
        defrost_start_mode = instrument.read_register(registeraddress=DEFROST_START_MODE_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        defrost_type_mode = instrument.read_register(registeraddress=DEFROST_TYPE_REIGSTER, number_of_decimals=0, functioncode=3, signed=False)

        if unit == 'F':
            t1_temperature = celsius_to_fahrenheit(t1_temperature)
            t2_temperature = celsius_to_fahrenheit(t2_temperature)
            setpoint_low = celsius_to_fahrenheit(setpoint_low)
            setpoint_high = celsius_to_fahrenheit(setpoint_high)
            setpoint = celsius_to_fahrenheit(setpoint)

        response = {
            "timestamp": get_current_timestamp(),
            "unit": unit,
            "status": {
                "evap_fan_status": "ON" if bool(evaporator_fan_status) else "OFF",
                "compressor_status": "ON" if bool(compressor_status) else "OFF",
                "door_heater_status": "ON" if bool(door_heater_status) else "OFF",
                "cabinet_lights_status": "ON" if bool(cabinet_lights_status) else "OFF",
                "defrost_status": "ON" if bool(defrost_status) else "OFF"
            },
            "defrost": {
                "defrost_start_mode": DEFROST_START_MODE_MAP[defrost_start_mode],
                "defrost_type": DEFROST_TYPE_MAP[defrost_type_mode]
            },
            "temperatures": {
                "T1": t1_temperature,
                "T2": t2_temperature
            },
            "setpoints": {
                "SPL": setpoint_low,
                "SP": setpoint,
                "SPH": setpoint_high
            },
            "differentials": {
                "HY0": hy0,
                "HY1": hy1
            },
            "standby_mode": "ON" if bool(standby_mode_status) else "OFF"
        }

        return jsonify(response), 200
    except Exception as e: 
        return jsonify({
            "error": str(e)
        }), 500

@cabinet_blueprint.route('/cabinet/temperatures', methods = ["GET"])
async def get_all_temperatures(device_id):
    """
    Gets the temperatures of the cold cabinet

    This endpoint retrieves the following temperatures of the cold cabinet,
        - Set Point Low (SPL), (Celsius or Fahrenheit)
        - Set Point High (SPL), (Celsius or Fahrenheit)
        - Set Point (SP), (Celsius or Fahrenheit)
        - T1
        - T2

    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Query Parameters:
        unit (str): Optional. Specify the temperature unit
            - 'C' for Celsius (default)
            - 'F' for Fahrenheit
    
    Returns:
        JSON response with the current temperatures, and a timestamp
    """
    validate_device_id(device_id, rs485_device_collection)

    unit = request.args.get('unit', default='C', type=str).upper()
    
    if unit not in ['C', 'F']:
        return jsonify({"error": "Invalid unit specified. Use 'C' for Celsius or 'F' for Fahrenheit."}), 400
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        # Setpoints
        setpoint_low = instrument.read_register(registeraddress=SETPOINT_LOW_REGISTER, number_of_decimals=1, functioncode=3, signed=True)
        setpoint_high = instrument.read_register(registeraddress=SETPOINT_HIGH_REGISTER, number_of_decimals=1, functioncode=3, signed=True)
        setpoint = instrument.read_register(registeraddress=SETPOINT_REGISTER, number_of_decimals=1, functioncode=3, signed=True)
        
        # Differentials
        t1_temperature = instrument.read_register(registeraddress=T1_AIR_PROBE_TEMPERATURE_REGISTER, number_of_decimals=1, functioncode=3, signed=True)
        t2_temperature = instrument.read_register(registeraddress=T2_EVAPORATOR_PROBE_TEMPERATURE_REGISTER, number_of_decimals=1, functioncode=3, signed=True)

        if unit == 'F':
            t1_temperature = celsius_to_fahrenheit(t1_temperature)
            t2_temperature = celsius_to_fahrenheit(t2_temperature)
            setpoint_low = celsius_to_fahrenheit(setpoint_low)
            setpoint_high = celsius_to_fahrenheit(setpoint_high)
            setpoint = celsius_to_fahrenheit(setpoint)

        response = {
            "timestamp": get_current_timestamp(),
            "unit": unit,
            "temperatures": {
                "T1": t1_temperature,
                "T2": t2_temperature
            },
            "setpoints": {
                "SPL": setpoint_low,
                "SP": setpoint,
                "SPH": setpoint_high
            },
        }

        return jsonify(response), 200
    except Exception as e: 
        return jsonify({
            "error": str(e)
        }), 500

@cabinet_blueprint.route('/cabinet/standby/on', methods = ["POST"])
async def enable_cabinet_standby(device_id):
    validate_device_id(device_id, rs485_device_collection)

    unit = request.args.get('unit', default='C', type=str).upper()
    
    if unit not in ['C', 'F']:
        return jsonify({"error": "Invalid unit specified. Use 'C' for Celsius or 'F' for Fahrenheit."}), 400
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        standby_enabled = instrument.read_register(registeraddress=STANDBY_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        if standby_enabled:
            return jsonify({
                "status": "Device is already on standby mode"
            }), 200
        
        instrument.write_register(registeraddress=STANDBY_REGISTER, value=int(1), number_of_decimals=0, functioncode=6, signed=False)

        # Read status for the following
        evaporator_fan_status = instrument.read_register(registeraddress=EVAPORATOR_FAN_OUTPUT_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        compressor_status = instrument.read_register(registeraddress=COMPRESSOR_OUTPUT_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        door_heater_status = instrument.read_register(registeraddress=AUXILLARY_OUTPUT_1_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        defrost_status = instrument.read_register(registeraddress=DEFROST_OUTPUT_REGISTRER, number_of_decimals=0, functioncode=3, signed=False)
        
        response = {
            "timestamp": get_current_timestamp(),
            "status": {
                "evap_fan_status": "ON" if bool(evaporator_fan_status) else "OFF",
                "compressor_status": "ON" if bool(compressor_status) else "OFF",
                "door_heater_status": "ON" if bool(door_heater_status) else "OFF",
                "defrost_status": "ON" if bool(defrost_status) else "OFF"
            },
            "standby_mode": "ON"
        }

        return jsonify(response), 200
        
    except Exception as e: 
        return jsonify({
            "error": str(e)
        }), 500

@cabinet_blueprint.route('/cabinet/standby/off', methods = ["POST"])
async def disable_cabinet_standby(device_id):
    validate_device_id(device_id, rs485_device_collection)

    unit = request.args.get('unit', default='C', type=str).upper()
    
    if unit not in ['C', 'F']:
        return jsonify({"error": "Invalid unit specified. Use 'C' for Celsius or 'F' for Fahrenheit."}), 400
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        standby_enabled = instrument.read_register(registeraddress=STANDBY_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        if not standby_enabled:
            return jsonify({
                "status": "Device is already not on standby mode"
            }), 200
        
        instrument.write_register(registeraddress=STANDBY_REGISTER, value=int(0), number_of_decimals=0, functioncode=6, signed=False)

        # Read status for the following
        evaporator_fan_status = instrument.read_register(registeraddress=EVAPORATOR_FAN_OUTPUT_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        compressor_status = instrument.read_register(registeraddress=COMPRESSOR_OUTPUT_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        door_heater_status = instrument.read_register(registeraddress=AUXILLARY_OUTPUT_1_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        defrost_status = instrument.read_register(registeraddress=DEFROST_OUTPUT_REGISTRER, number_of_decimals=0, functioncode=3, signed=False)
        
        response = {
            "timestamp": get_current_timestamp(),
            "status": {
                "evap_fan_status": "ON" if bool(evaporator_fan_status) else "OFF",
                "compressor_status": "ON" if bool(compressor_status) else "OFF",
                "door_heater_status": "ON" if bool(door_heater_status) else "OFF",
                "defrost_status": "ON" if bool(defrost_status) else "OFF"
            },
            "standby_mode": "OFF"
        }

        return jsonify(response), 200
        
    except Exception as e: 
        return jsonify({
            "error": str(e)
        }), 500

@cabinet_blueprint.route('/cabinet/light/on', methods = ["POST"])
async def turn_cabinet_lights_on(device_id):
    validate_device_id(device_id, rs485_device_collection)
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        lights_enabled = instrument.read_register(registeraddress=LIGHTS_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        if lights_enabled:
            return jsonify({
                "status": "Lights for the cabinet already on"
            }), 200
        
        instrument.write_register(registeraddress=LIGHTS_REGISTER, value=int(1), number_of_decimals=0, functioncode=6, signed=False)
        
        response = {
            "timestamp": get_current_timestamp(),
            "cabinet_lights_status": "ON"
        }

        return jsonify(response), 200
        
    except Exception as e: 
        return jsonify({
            "error": str(e)
        }), 500


@cabinet_blueprint.route('/cabinet/light/off', methods = ["POST"])
async def turn_cabinet_lights_off(device_id):
    validate_device_id(device_id, rs485_device_collection)
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        lights_enabled = instrument.read_register(registeraddress=LIGHTS_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        if not lights_enabled:
            return jsonify({
                "status": "Lights for the cabinet already off"
            }), 200
        
        instrument.write_register(registeraddress=LIGHTS_REGISTER, value=int(0), number_of_decimals=0, functioncode=6, signed=False)
        
        response = {
            "timestamp": get_current_timestamp(),
            "cabinet_lights_status": "OFF"
        }

        return jsonify(response), 200
        
    except Exception as e: 
        return jsonify({
            "error": str(e)
        }), 500

