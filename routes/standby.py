from quart import Blueprint, jsonify, request
from utils.helpers import (
    create_instrument,
    get_current_timestamp
)
from utils.validators import (
    validate_device_id
)

MANUAL_STANDBY_REGISTER = 700   # Register for Manual Standby (enable/disable the power button on display)
STANDBY_REGISTER = 701          # Register for Standby (set on/off for standby)

standby_blueprint = Blueprint("standby", __name__)
rs485_device_collection = None
rs485_device_settings_collection = None

def init_app(app, db):
    global rs485_device_collection
    global rs485_device_settings_collection
    rs485_device_collection = db['rs485_devices']
    rs485_device_settings_collection = db['rs485_device_controller_settings']

# Routes
@standby_blueprint.route('/standby', methods = ["GET"])
async def read_standby_status(device_id):
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
        standby_mode_enabled = instrument.read_register(registeraddress=STANDBY_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        return jsonify({
            "status": "Device is currently in Standby Mode" if bool(standby_mode_enabled) else "Device is not currently in Standby Mode",
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@standby_blueprint.route('/standby/on', methods = ["POST"])
async def turn_standby_on(device_id):
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
async def turn_standby_off(device_id):
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

@standby_blueprint.route('/standby/manual', methods = ["GET"])
async def get_manual_standby_status(device_id):
    """
    Gets the status of the manual standby mode from the temperature controller display

    This endpoint checks status of standby mode from the temperature controller display, it is the power button
    on the actual power display
    """
    validate_device_id(device_id, rs485_device_collection)

    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({
            "error": "Failed to create instrument"
        }), 500
    
    try:
        manual_standby_mode_enabled = instrument.read_register(registeraddress=MANUAL_STANDBY_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        return jsonify({
            "manual_standby_status": "enabled" if bool(manual_standby_mode_enabled) else "disabled",
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
    
@standby_blueprint.route('/standby/manual/on', methods = ["POST"])
async def enable_manual_standby(device_id):
    validate_device_id(device_id, rs485_device_collection)

    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({
            "error": "Failed to create instrument"
        }), 500
    
    try:
        manual_standby_mode_enabled = instrument.read_register(registeraddress=MANUAL_STANDBY_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        if manual_standby_mode_enabled:
            return jsonify({
                "status": "Device is already has manual standby mode enabled"
            }), 200
        
        instrument.write_register(registeraddress=STANDBY_REGISTER, value=int(1), number_of_decimals=0, functioncode=6, signed=False)
        return jsonify({
            "manual_standby_status": "enabled",
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e: 
        return jsonify({
            "error": str(e)
        }), 500

@standby_blueprint.route('/standby/manual/off', methods = ["POST"])
async def disable_manual_standby(device_id):
    validate_device_id(device_id, rs485_device_collection)

    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({
            "error": "Failed to create instrument"
        }), 500
    
    try:
        manual_standby_enabled = instrument.read_register(registeraddress=MANUAL_STANDBY_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        if not manual_standby_enabled:
            return jsonify({
                "status": "Device has already disabled manual standby mode"
            }), 200
        
        instrument.write_register(registeraddress=MANUAL_STANDBY_REGISTER, value=int(0), number_of_decimals=0, functioncode=6, signed=False)
        
        return jsonify({
            "manual_standby_status": "disabled",
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e: 
        return jsonify({
            "error": str(e)
        }), 500
