from quart import Blueprint, jsonify, request
from utils.helpers import (
    create_instrument, 
    get_current_timestamp,
)
from utils.validators import (
    validate_device_id
)

# HY0 and HY1 Registers
HY0_REGISTER = 204  # Compressor Off to On, R/W
HY1_REGISTER = 205  # Compressor On to Off, R/W
CRT_REGISTER = 206  # Compressor rest time (minutes)

compressor_blueprint = Blueprint('compressor', __name__)
rs485_device_collection = None
rs485_device_settings_collection = None

def init_app(app, db):
    global rs485_device_collection
    global rs485_device_settings_collection
    rs485_device_collection = db['rs485_devices']
    rs485_device_settings_collection = db['rs485_device_controller_settings']

@compressor_blueprint.route('/compressor/hy0', methods=["POST"])
async def set_hy0_differential(device_id):
    """
    Set the HY0 differential for compressor (Off to On)

    This endpoint allows you to set the differential for when the compressor should turn on
    
    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Parameters:
        - differential (float): The desired differential, should be between 1 and 10
    
    Returns:
        - JSON response with the newly set HY0 differential and a timestamp
    """
    data = await request.get_json()
    if data is None: 
        return jsonify({"error": "Invalid JSON"}), 500
    
    validate_device_id(device_id, rs485_device_collection)

    hy0_differential = int(data.get("differential"))
    if hy0_differential is None:
        return jsonify({"error": "Differential value is required"}), 400
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        if not (1.0 <= hy0_differential <= 10):
           return jsonify({
                "error": "Differential must be betweeen 1.0 and 10.0"
            }), 400
        
        instrument.write_register(registeraddress=HY0_REGISTER, value=int(hy0_differential), number_of_decimals=0, functioncode=6, signed=False)
        
        return jsonify({
            "HY0": hy0_differential,
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@compressor_blueprint.route('/compressor/hy0', methods=["GET"])
async def read_hy0_differential(device_id):
    """
    Read the current HY0 differential.

    This endpoint retrieves the current HY0 differential for when the compressor should turn on.

    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Returns:
        JSON response with the current HY0 differential value and a timestamp.
    """
    validate_device_id(device_id, rs485_device_collection)

    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        hy0_differential = instrument.read_register(registeraddress=HY0_REGISTER, number_of_decimals=0, functioncode=3, signed=False)

        return jsonify({
            "HY0": hy0_differential,
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@compressor_blueprint.route('/compressor/hy1', methods=["POST"])
async def set_hy1_differential(device_id):
    """
    Set the HY1 differential for compressor (On to Off)

    This endpoint allows you to set the differential for when the compressor should turn off

    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Parameters:
        - differential (float): The desired differential, should be between 0 and 10
    
    Returns:
        - JSON response with the newly set differential and a timestamp
    """
    data = await request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON"}), 500
    
    validate_device_id(device_id, rs485_device_collection)

    hy1_differential = int(data.get("differential"))
    if hy1_differential is None:
        return jsonify({"error": "Differential value is required"}), 400
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        if not (0.0 <= hy1_differential <= 10):
           return jsonify({
                "error": "Differential must be betweeen 0.0 and 10.0"
            }), 400
        
        instrument.write_register(registeraddress=HY1_REGISTER, value=int(hy1_differential), number_of_decimals=0, functioncode=6, signed=False)
        
        return jsonify({
            "HY1": hy1_differential,
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
    
@compressor_blueprint.route('/compressor/hy1', methods=["GET"])
async def read_hy1_differential(device_id):
    """
    Read the current HY1 differential.

    This endpoint retrieves the current HY1 differential for when the compressor should turn off.

    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Returns:
        JSON response with the current HY1 differential value and a timestamp.
    """
    validate_device_id(device_id, rs485_device_collection)

    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        hy1_differential = instrument.read_register(registeraddress=HY1_REGISTER, number_of_decimals=0, functioncode=3, signed=False)

        return jsonify({
            "HY1": hy1_differential,
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@compressor_blueprint.route('/compressor/rest-time', methods=["POST"])
async def set_compressor_rest_time(device_id):
    """
    Sets the rest time for compressor

    This endpoint allows you to set the rest time for a compressor

    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Parameters:
        - rest_time (int): The desired rest time in minutes, should be between 0 and 30
    
    Returns:
        - JSON response with the newly set rest time and a timestamp
    """
    data = await request.get_json()
    if data is None: 
        return jsonify({"error": "Invalid JSON"}), 500
    validate_device_id(device_id, rs485_device_collection)

    crt = int(data.get("rest_time"))
    if crt is None:
        return jsonify({"error": "Rest time value is required"}), 400
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        if not (0 <= crt <= 30):
           return jsonify({
                "error": "Compressor rest time must be betweeen 0 and 30"
            }), 400
        
        instrument.write_register(registeraddress=CRT_REGISTER, value=int(crt), number_of_decimals=0, functioncode=6, signed=False)
        
        return jsonify({
            "CRT": crt,
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@compressor_blueprint.route('/compressor/rest-time', methods=["GET"])
async def read_compressor_rest_time(device_id):
    """
    Read the current compressor rest time.

    This endpoint retrieves the current rest time (minutes) of a compressor.

    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Returns:
        JSON response with the current compressor rest time and a timestamp.
    """
    validate_device_id(device_id, rs485_device_collection)
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    try:
        crt = instrument.read_register(registeraddress=CRT_REGISTER, number_of_decimals=0, functioncode=3, signed=False)

        return jsonify({
            "CRT": crt,
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500