from flask import Blueprint, jsonify, request
from utils.helpers import (
    create_instrument,
    get_current_timestamp
)
from utils.validators import (
    validate_device_id
)

STANDBY_REGISTER = 700          # Register for Standby (set on/off for standby)
MANUAL_STANDBY_REGISTER = 701   # Register for Manual Standby (enable/disable the power button on display)

standby_blueprint = Blueprint("standby", __name__, url_prefix='/standby')
rs485_device_collection = None
rs485_device_settings_collection = None

def init_app(app, db):
    global rs485_device_collection
    global rs485_device_settings_collection
    rs485_device_collection = db['rs485_devices']
    rs485_device_settings_collection = db['rs485_device_controller_settings']

# Routes
@standby_blueprint.route('/standby', methods = ["GET"])
def read_standby_status(device_id):
    """
    Reads if the device is on standby mode or not

    This endpoint checks the current status of the controller, and returns true if the controller is on standby mode (off),
    or not (on).

    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Returns:
        JSON response with standby mode status of the controller, and a timestamp
    """
    validate_device_id(device_id, rs485_device_collection)

    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({
            "error": "Failed to create instrument"
        }), 500
    
    try:
        stanby_mode_enabled = instrument.read_register(registeraddress=STANDBY_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        return jsonify({
            "status": "Device is currently in Standby Mode" if bool(stanby_mode_enabled) else "Device is not currently in Standby Mode",
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@standby_blueprint.route('/standby/on', methods = ["POST"])
def turn_standby_on(device_id):
    validate_device_id(device_id, rs485_device_collection)

    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({
            "error": "Failed to create instrument"
        }), 500
    
    try:
        standby_enabled = instrument.read_register(registeraddress=STANDBY_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        if standby_enabled:
            return jsonify({
                "status": "Device is already on standby mode"
            }), 200
        
        instrument.write_register(registeraddress=STANDBY_REGISTER, value=int(1), number_of_decimals=0, functioncode=6, signed=False)
        
        return jsonify({
            "status": "Standby Mode is on",
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e: 
        return jsonify({
            "error": str(e)
        }), 500

@standby_blueprint.route('/standby/off', methods = ["POST"])
def turn_standby_on(device_id):
    validate_device_id(device_id, rs485_device_collection)

    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({
            "error": "Failed to create instrument"
        }), 500
    
    try:
        standby_enabled = instrument.read_register(registeraddress=STANDBY_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        if not standby_enabled:
            return jsonify({
                "status": "Device is already not in standby mode"
            }), 200
        
        instrument.write_register(registeraddress=STANDBY_REGISTER, value=int(0), number_of_decimals=0, functioncode=6, signed=False)
        
        return jsonify({
            "status": "Standby Mode is off",
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e: 
        return jsonify({
            "error": str(e)
        }), 500

@standby_blueprint.route('/status/manual', methods = ["GET"])
def get_manual_standby_status(device_id):
    """
    Gets the status of the manual standby mode from the temperature controller display

    This endpoint checks status of standby mode from the temperature controller display
    """    
