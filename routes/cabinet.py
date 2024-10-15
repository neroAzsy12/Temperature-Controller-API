from flask import Blueprint, jsonify, request
from utils.helpers import (
    create_instrument,
    get_current_timestamp,  
    celsius_to_fahrenheit
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

cabinet_blueprint = Blueprint('cabinet', __name__)
rs485_device_collection = None
rs485_device_settings_collection = None

def init_app(app, db):
    global rs485_device_collection
    global rs485_device_settings_collection
    rs485_device_collection = db['rs485_devices']
    rs485_device_settings_collection = db['rs485_device_controller_settings']

@cabinet_blueprint.route('/cabinet/status', methods = ["GET"])
def get_cabinet_status(device_id):
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
        t1_temperature = instrument.read_register(registeraddress=T1_AIR_PROBE_TEMPERATURE_REGISTER, number_of_decimals=1, functioncode=3, signed=True)
        t2_temperature = instrument.read_register(registeraddress=T2_EVAPORATOR_PROBE_TEMPERATURE_REGISTER, number_of_decimals=1, functioncode=3, signed=True)

        if unit == 'F':
            t1_temperature = celsius_to_fahrenheit(t1_temperature)
            t2_temperature = celsius_to_fahrenheit(t2_temperature)
        
        evaporator_fan_status = instrument.read_register(registeraddress=EVAPORATOR_FAN_OUTPUT_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        compressor_status = instrument.read_register(registeraddress=COMPRESSOR_OUTPUT_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        defrost_status = instrument.read_register(registeraddress=DEFROST_OUTPUT_REGISTRER, number_of_decimals=0, functioncode=3, signed=False)

        response = {
            "timestamp": get_current_timestamp(),
            "unit": unit,
            "evap_fan_status": "ON" if bool(evaporator_fan_status) else "OFF",
            "compressor_status": "ON" if bool(compressor_status) else "OFF",
            "defrost_status": "ON" if bool(defrost_status) else "OFF",
            "temperatures": {
                "T1": t1_temperature,
                "T2": t2_temperature
            }
        }

        return jsonify(response), 200
    except Exception as e: 
        return jsonify({
            "error": str(e)
        }), 500
