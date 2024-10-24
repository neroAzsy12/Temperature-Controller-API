from quart import Blueprint, jsonify, request
from utils.helpers import (
    create_instrument,
    get_current_timestamp, 
    celsius_to_fahrenheit, 
    fahrenheit_to_celsius
)
from utils.validators import (
    validate_device_id
)

# Setpoint Registers
T2_EVAPORATOR_PROBE_TEMPERATURE_REGISTER = 1
DEFROST_OUTPUT_REGISTER = 139           # Register for current defrost status (on/off)
DEFROST_ENABLED_REGISTER = 400          # Register for starting/ending defrost
DEFROST_BIT = 4                         # Bit for accessing defrost (on/off)
DEFROST_END_TEMPERATURE_REGISTER = 211  #
DEFROST_START_MODE_REGISTER = 209
DEFROST_START_MODE_MAP = {
    0: {
        "type": "NON",
        "description": "Defrost disabled"
    },
    1: {
        "type": "TIM",
        "description": "Regular time defrost"
    },
    2: {
        "type": "FRO",
        "description": "Frost accumulation"
    },
    3: {
        "type": "RTC",
        "description": "Defrost scheduled by DH1...DH6"
    }
}

DEFROST_TYPE_REIGSTER = 213
DEFROST_TYPE_MAP = {
    0: {
        "type": "OFF",
        "description": "Compressor on, Defrost off"
    },
    1: {
        "type": "ELE",
        "description": "Compressor off, Defrost on"
    },
    2: {
        "type": "GAS",
        "description": "Compressor on, Defrost on"
    }
}
DEFROST_DISPLAY_REGISTER = 218
DEFROST_DISPLAY_MAP = {
    0: {
        "type": "RT",
        "description": "Actual air temperature"
    },
    1: {
        "type": "LT",
        "description": "Last temperature display before defrost start"
    },
    2: {
        "type": "SP",
        "description": "Current setpoint value"
    },
    3: {
        "type": "DEF",
        "description": "Display DEF"
    }
}

defrost_blueprint = Blueprint('defrost', __name__)
rs485_device_collection = None
rs485_device_settings_collection = None

def init_app(app, db):
    global rs485_device_collection
    global rs485_device_settings_collection
    rs485_device_collection = db['rs485_devices']
    rs485_device_settings_collection = db['rs485_device_controller_settings']

@defrost_blueprint.route('/defrost/status', methods = ["GET"])
async def get_defrost_status(device_id):
    validate_device_id(device_id, rs485_device_collection)

    unit = request.args.get('unit', default='C', type=str).upper()
    if unit not in ['C', 'F']:
        return jsonify({"error": "Invalid unit specified. Use 'C' for Celsius or 'F' for Fahrenheit."}), 400

    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        defrost_status = instrument.read_register(registeraddress=DEFROST_OUTPUT_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        defrost_start_mode = instrument.read_register(registeraddress=DEFROST_START_MODE_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        defrost_type = instrument.read_register(registeraddress=DEFROST_TYPE_REIGSTER, number_of_decimals=0, functioncode=3, signed=False)
        defrost_display = instrument.read_register(registeraddress=DEFROST_DISPLAY_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        defrost_end_temperature = instrument.read_register(registeraddress=DEFROST_END_TEMPERATURE_REGISTER, number_of_decimals=1, functioncode=3, signed=True)

        if unit == 'F':
            defrost_end_temperature = celsius_to_fahrenheit(defrost_end_temperature)

        response = {
            "timestamp": get_current_timestamp(),
            "status": "ON" if bool(defrost_status) else "OFF",
            "start_mode": {
                "mode": DEFROST_START_MODE_MAP[defrost_start_mode]["type"],
                "description": DEFROST_START_MODE_MAP[defrost_start_mode]["description"]
            },
            "type": {
                "type": DEFROST_TYPE_MAP[defrost_type]["type"],
                "description": DEFROST_TYPE_MAP[defrost_type]["description"]
            },
            "display": {
                "mode": DEFROST_DISPLAY_MAP[defrost_display]["type"],
                "description": DEFROST_DISPLAY_MAP[defrost_display]["description"]
            },
            "end_temperature": defrost_end_temperature
        }

        return jsonify(response), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
    
@defrost_blueprint.route('/defrost/on', methods = ["POST"])
async def turn_defrost_on(device_id):
    validate_device_id(device_id, rs485_device_collection)
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        defrost_enabled = instrument.read_register(registeraddress=DEFROST_OUTPUT_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        if defrost_enabled:
            return jsonify({
                "status": "Cabinet is already in defrost mode"
            }), 200
        
        defrost_status = instrument.read_register(registeraddress=DEFROST_ENABLED_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        defrost_status |= (1 << DEFROST_BIT)

        instrument.write_register(registeraddress=DEFROST_ENABLED_REGISTER, value=int(defrost_status), number_of_decimals=0, functioncode=6, signed=False)

        return jsonify({
            "status": 'enabled',
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@defrost_blueprint.route('/defrost/off', methods = ["POST"])
async def turn_defrost_off(device_id):
    validate_device_id(device_id, rs485_device_collection)
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        defrost_enabled = instrument.read_register(registeraddress=DEFROST_OUTPUT_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        if not defrost_enabled:
            return jsonify({
                "status": "Cabinet is already not in defrost mode"
            }), 200
        
        current_t2_temperature = instrument.read_register(registeraddress=T2_EVAPORATOR_PROBE_TEMPERATURE_REGISTER, number_of_decimals=1, functioncode=3, signed=True)
        current_defrost_end_temperature = instrument.read_register(registeraddress=DEFROST_END_TEMPERATURE_REGISTER, number_of_decimals=1, functioncode=3, signed=True)

        instrument.write_register(registeraddress=DEFROST_END_TEMPERATURE_REGISTER, value=float(current_t2_temperature), number_of_decimals=1, functioncode=6, signed=True)
        defrost_status = instrument.read_register(registeraddress=DEFROST_ENABLED_REGISTER, number_of_decimals=0, functioncode=3, signed=False)
        defrost_status &= ~(1 << DEFROST_BIT)

        instrument.write_register(registeraddress=DEFROST_ENABLED_REGISTER, value=int(defrost_status), number_of_decimals=0, functioncode=6, signed=False)
        instrument.write_register(registeraddress=DEFROST_END_TEMPERATURE_REGISTER, value=float(current_defrost_end_temperature), number_of_decimals=1, functioncode=6, signed=True)

        return jsonify({
            "status": 'disabled',
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@defrost_blueprint.route('/defrost/start-mode', methods = ['POST'])
async def set_defrost_start_mode(device_id):
    data = await request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON"}), 500
    
    validate_device_id(device_id, rs485_device_collection)
    
    start_mode = int(data.get("start_mode")) 
    if start_mode is None:
        return jsonify({"error": "Start Mode for defrost is required"}), 400

    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try: 
        if not (0 <= start_mode <= 3):
            return jsonify({
                "error": "start_mode must be between 0 and 3"
                }), 400
        
        instrument.write_register(registeraddress=DEFROST_START_MODE_REGISTER, value=int(start_mode), number_of_decimals=0, functioncode=6, signed=False)

        return jsonify({
            "timestamp": get_current_timestamp(),
            "mode": DEFROST_START_MODE_MAP[start_mode]["type"],
            "description": DEFROST_START_MODE_MAP[start_mode]["description"]
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@defrost_blueprint.route('/defrost/type', methods = ['POST'])
async def set_defrost_type(device_id):
    data = await request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON"}), 500 
    
    validate_device_id(device_id)

    defrost_type = int(data.get("defrost_type"))
    if defrost_type is None:
        return jsonify({"error": "Defrost type is required"}), 400
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        if not (0 <= defrost_type <= 2):
            return jsonify({
                "error": "defrost_type must be between 0 and 2"
            }), 400
        
        instrument.write_register(registeraddress=DEFROST_TYPE_REIGSTER, value=int(defrost_type), number_of_decimals=0, functioncode=6, signed=False)

        return jsonify({
            "timestamp": get_current_timestamp(),
            "defrost_type": DEFROST_TYPE_MAP[defrost_type]['type'],
            "description": DEFROST_TYPE_MAP[defrost_type]['description']
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
    
@defrost_blueprint.route('/defrost/display', methods = ['POST'])
async def set_defrost_display(device_id):
    data = await request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON"}), 500
    
    validate_device_id(device_id)

    display_mode = int(data.get("display"))
    if display_mode is None:
        return jsonify({"error": "Display Mode for defrost is required"}), 400
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        if not (0 <= display_mode <= 3):
            return jsonify({
                "error": "display must be between 0 and 3"
            }), 400
        
        instrument.write_register(registeraddress=DEFROST_DISPLAY_REGISTER, value=int(display_mode), number_of_decimals=0, functioncode=6, signed=False)
        
        return jsonify({
            "timestamp": get_current_timestamp(),
            "display_mode": DEFROST_DISPLAY_MAP[display_mode]['type'],
            "description": DEFROST_DISPLAY_MAP[display_mode]['description']
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500