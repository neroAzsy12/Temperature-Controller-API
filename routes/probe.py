from flask import Blueprint, jsonify, request
from utils.helpers import (
    DEVICE01_CONTROLLER_SETTINGS_FILE_PATH,
    create_instrument,
    get_current_timestamp,  
    celsius_to_fahrenheit
)
from utils.validators import (
    validate_device_id
)

# Probe configurations
T1_AIR_PROBE_TEMPERATURE_REGISTER = 0           # Register for reading temperature from T1
T2_EVAPORATOR_PROBE_TEMPERATURE_REGISTER = 1    # Register for reading temperature from T2
T2_ENABLED_REGISTER = 705                       # Register for enabling/disabling T2 probe, as well as checking the status

probe_blueprint = Blueprint('probe', __name__)
rs485_device_collection = None
rs485_device_settings_collection = None

def init_app(app, db):
    global rs485_device_collection
    global rs485_device_settings_collection
    rs485_device_collection = db['rs485_devices']
    rs485_device_settings_collection = db['rs485_device_controller_settings']

# Routes
@probe_blueprint.route('/probe/temperature/t1', methods = ["GET"])
def read_temperature_t1(device_id):
    """
    Read the current Air probe temperature (T1)

    This endpoint retrieves the current temperature from Probe T1 and returns it in the specified unit (Celsius or Fahrenheit)
    along with a timestamp, and T1

    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Query Parameters:
        unit (str): Optional. Specify the temperature unit:
            - 'C' for Celsius (default)
            - 'F' for Fahrenheit

    Returns:
        JSON response with the current temperature from Probe T1 in the specified unit and a timestamp
    """
    validate_device_id(device_id, rs485_device_collection)

    unit = request.args.get('unit', default='C', type=str).upper()
    
    if unit not in ['C', 'F']:
        return jsonify({"error": "Invalid unit specified. Use 'C' for Celsius or 'F' for Fahrenheit."}), 400
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        temperature = instrument.read_register(registeraddress=T1_AIR_PROBE_TEMPERATURE_REGISTER, number_of_decimals=1, functioncode=3, signed=True)

        if unit == 'F':
            temperature = celsius_to_fahrenheit(temperature)

        timestamp = get_current_timestamp()
        return jsonify({
            "temperature": temperature,
            "unit": unit,
            "probe": "T1",
            "timestamp": timestamp
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@probe_blueprint.route('/probe/temperature/t2', methods=["GET"])
def read_temperature_t2(device_id):
    """
    Read the Evaporator probe temperature (T2)

    This endpoint retrieves the current temperature from Probe T2 and returns it in the specified unit (Celsius or Fahrenheit)
    along with a timestamp, and T2

    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Query Parameters:
        unit (str): Optional. Specify the temperature unit:
            - 'C' for Celsius (default)
            - 'F' for Fahrenheit

    Returns:
        JSON response with the current temperature from Probe T2 in the specified unit and a timestamp
    """
    validate_device_id(device_id, rs485_device_collection)

    unit = request.args.get('unit', default='C', type=str).upper()
    
    if unit not in ['C', 'F']:
        return jsonify({"error": "Invalid unit specified. Use 'C' for Celsius or 'F' for Fahrenheit."}), 400
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        # Check if the probe T2 is enabled
        probe_enabled = instrument.read_register(registeraddress=T2_ENABLED_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        if not probe_enabled:
            return jsonify({
                "error": "Probe is disabled. Cannot read temperature."
            }), 400
        
        temperature = instrument.read_register(registeraddress=T2_EVAPORATOR_PROBE_TEMPERATURE_REGISTER, number_of_decimals=1, functioncode=3, signed=True)

        if unit == 'F':
            temperature = celsius_to_fahrenheit(temperature)

        return jsonify({
            "temperature": temperature,
            "unit": unit,
            "probe": "T2",
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
    
@probe_blueprint.route('/probe/status/t2', methods=["GET"])
def get_t2_probe_status(device_id):
    """
    Checks the status of Probe T2

    This endpoint retrieves the status of Probe T2 (enabled or disabled).

    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Returns:
        - JSON response the status of Probe T2, and a timestamp
    """
    validate_device_id(device_id, rs485_device_collection)

    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({
            "error": "Failed to create instrument"
        }), 500
    
    try:
        probe_enabled = instrument.read_register(registeraddress=T2_ENABLED_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        return jsonify({
            "enabled": bool(probe_enabled),
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
    
@probe_blueprint.route("/probe/enable/t2", methods=["POST"])
def enable_probe_t2(device_id):
    """
    Enable T2 probe

    This endpoint enablenables the t2 probe if it is currently disabled
    
    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Returns:
        JSON: A JSON object indicating that probe T2 has been enabled or was already enabled and a timestamp
    """
    validate_device_id(device_id, rs485_device_collection)

    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({
            "error": "Failed to create instrument"
        }), 500
    
    try:
        probe_enabled = instrument.read_register(registeraddress=T2_ENABLED_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        if probe_enabled:
            return jsonify({
                "status": "T2 probe is already enabled."
            }), 200
        
        instrument.write_register(registeraddress=T2_ENABLED_REGISTER, value=1, number_of_decimals=0, functioncode=6, signed=False)
        timestamp = get_current_timestamp()

        # update device-controller-settings
        rs485_device_settings_collection.update_one(
            {"device_name": device_id},     # Query to find the item
            {"$set": {"isT2Enabled": True}} # Update the specific field
        )

        return jsonify({
            "status": "enabled",
            "timestamp": timestamp
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@probe_blueprint.route("/probe/disable/t2", methods=["POST"])
def disable_probe_t2(device_id):
    """
    Disable T2 probe

    This endpoint disables the t2 probe if it is currently enabled
    
    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Returns:
        JSON: A JSON object indicating that probe T2 has been disabled or was already disabled and a timestamp
    """
    validate_device_id(device_id, rs485_device_collection)
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({
            "error": "Failed to create instrument"
        }), 500
    
    try:
        probe_enabled = instrument.read_register(registeraddress=T2_ENABLED_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        if not probe_enabled:
            return jsonify({
                "status": "T2 probe is already disabled."
            }), 200
        
        instrument.write_register(registeraddress=T2_ENABLED_REGISTER, value=0, number_of_decimals=0, functioncode=6, signed=False)
        timestamp = get_current_timestamp()

        rs485_device_settings_collection.update_one(
            {"device_name": device_id},
            {"$set": {"isT2Enabled": False}}
        )

        return jsonify({
            "status": "disabled",
            "timestamp": timestamp
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500