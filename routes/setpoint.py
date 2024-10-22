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
MINIMUM_SETPOINT_REGISTER = 201 # Register for minimum setpoint temperature
MAXIMUM_SETPOINT_REGISTER = 202 # Register for maximum setpoint temperature
SETPOINT_REGISTER = 203         # Register for setpoint temperature

setpoint_blueprint = Blueprint('setpoint', __name__)
rs485_device_collection = None
rs485_device_settings_collection = None

def init_app(app, db):
    global rs485_device_collection
    global rs485_device_settings_collection
    rs485_device_collection = db['rs485_devices']
    rs485_device_settings_collection = db['rs485_device_controller_settings']

# Routes
@setpoint_blueprint.route('/setpoint', methods=["POST"])
async def set_setpoint(device_id):
    """
    Set a new setpoint temperature

    This endpoint allows you to set a new temperature setpoint. The provided setpoint
    must be within range defined by the minimum and maximum setpoints. The unit of
    the temperature can be specified via a query parameter ('C' for Celsius or 'F' for Fahrenheit).
    
    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Parameters:
        - setpoint (float): The desired temperature setpoint to be set (in the request body)
        - unit (string): The unit of the setpoint ('C' or 'F') provided as a query parameter. Defaults to 'C'.

    Returns:
        - JSON response with status and new setpoint value (in the specified unit), the unit, and a timestamp if successful
        - Error message if the setpoint is out of range or if the input is invalid. 
    """
    validate_device_id(device_id, rs485_device_collection)

    new_setpoint = float(request.json.get('setpoint'))              # get from request body
    unit = request.args.get('unit', default='C', type=str).upper()  # get from query parameter

    if new_setpoint is None:
        return jsonify({"error": "Setpoint value is required"}), 400
    
    if unit not in ['C', 'F']:
        return jsonify({"error": "Invalid unit specified. Use 'C' for Celsius or 'F' for Fahrenheit."}), 400
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    # Read current min and max setpoints
    try:
        min_setpoint = instrument.read_register(registeraddress=MINIMUM_SETPOINT_REGISTER, number_of_decimals=1, functioncode=3, signed=True)
        max_setpoint = instrument.read_register(registeraddress=MAXIMUM_SETPOINT_REGISTER, number_of_decimals=1, functioncode=3, signed=True)

        # Convert min and max to the same unit as the new setpoint
        if unit == 'F':
            min_setpoint = celsius_to_fahrenheit(min_setpoint)
            max_setpoint = celsius_to_fahrenheit(max_setpoint)

        # Check if the new setpoint is within the allowed range
        if not (min_setpoint <= new_setpoint <= max_setpoint):
            return jsonify({
                "error": f"Setpoint must be betweeen {min_setpoint} and {max_setpoint} {unit}."
            }), 400
        
        # Convert new setpoint to Celsius before writing to the register
        celsius_setpoint = fahrenheit_to_celsius(new_setpoint) if unit == 'F' else new_setpoint
        instrument.write_register(registeraddress=SETPOINT_REGISTER, value=float(celsius_setpoint), number_of_decimals=1, functioncode=6, signed=True)

        result = rs485_device_settings_collection.find_one(
            {"device_name": device_id},
            {"currentMode": 1, "_id": 0}
        )

        mode = result['currentMode']

        rs485_device_settings_collection.update_one(
            {"device_name": device_id},
            {"$set": {f"{mode}.setpoint": celsius_setpoint}}
        )

        return jsonify({
            "status": "Setpoint updated",
            "setpoint": new_setpoint,
            "unit": unit,
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@setpoint_blueprint.route('/setpoint', methods=["GET"])
async def read_setpoint(device_id):
    """
    Read the current setpoint temperature.

    This endpoint retrieves the current temperature setpoint and returns it along with
    the unit that can be specified via a query parameter ('C' for Celsius or 'F' for Fahrenheit) and a timestamp.

    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Returns:
        JSON response with the current setpoint value in the specified unit and a timestamp.
    """
    validate_device_id(device_id, rs485_device_collection)

    unit = request.args.get('unit', default='C', type=str).upper()  # get from query parameter
    if unit not in ['C', 'F']:
        return jsonify({"error": "Invalid unit specified. Use 'C' for Celsius or 'F' for Fahrenheit."}), 400
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument."}), 500
   
    try:
        setpoint_value = instrument.read_register(registeraddress=SETPOINT_REGISTER, number_of_decimals=1, functioncode=3, signed=True)

        if unit == 'F':
            setpoint_value = celsius_to_fahrenheit(setpoint_value)
        
        return jsonify({
            "setpoint": setpoint_value,
            "unit": unit,
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@setpoint_blueprint.route('/setpoint/min', methods=["POST"])
async def set_min_setpoint(device_id):
    """
    Sets a new minimum setpoint temperature.

    This endpoint allows you to set a new minimum temperature setpoint. The provided minimum
    setpoint must be between -50°C (-58°F) and the current maximum setpoint. The unit of the temperature
    can be specified via a query parameter ('C' for Celsius or 'F' for Fahrenheit).
    
    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Parameters:
        - min_setpoint (float): The desired minimum temperature setpoint to be set (in the request body).
        - unit (string): The unit of the minimum setpoint ('C' or 'F') provided as a query parameter. Defaults to 'C'.

    Returns:
        - JSON response with status and new minimum setpoint value (in the specified unit), the unit, and a timestamp if successful
        - Error message if the setpoint is out of range or if the input is invalid. 
    """
    validate_device_id(device_id, rs485_device_collection)

    MIN_SETPOINT = -50                                              # Min setpoint allowed, -50 C (-58 F)
    new_min_setpoint = float(request.json.get('min_setpoint'))      # get from request body
    unit = request.args.get('unit', default='C', type=str).upper()  # get from query parameter

    if new_min_setpoint is None:
        return jsonify({"error": "Minimum setpoint value is required"}), 400
    
    if unit not in ['C', 'F']:
        return jsonify({"error": "Invalid unit specified. Use 'C' for Celsius or 'F' for Fahrenheit."}), 400
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    # Read current max setpoint
    try:
        max_setpoint = instrument.read_register(registeraddress=MAXIMUM_SETPOINT_REGISTER, number_of_decimals=1, functioncode=3, signed=True)
        
        # Convert MIN_SETPOINT and max_setpoint to the same unit as the new min setpoint
        if unit == 'F':
            max_setpoint = celsius_to_fahrenheit(max_setpoint)
            MIN_SETPOINT = -58

        # Check if the new setpoint is within the allowed range
        if not (MIN_SETPOINT <= new_min_setpoint <= max_setpoint):
            return jsonify({
                "error": f"Minimum setpoint must be betweeen {MIN_SETPOINT} and {max_setpoint} {unit}."
            }), 400
        
        celsius_min_setpoint = fahrenheit_to_celsius(new_min_setpoint) if unit == 'F' else new_min_setpoint
        instrument.write_register(registeraddress=MINIMUM_SETPOINT_REGISTER, value=float(celsius_min_setpoint), number_of_decimals=1, functioncode=6, signed=True)
        
        result = rs485_device_settings_collection.find_one(
            {"device_name": device_id},
            {"currentMode": 1, "_id": 0}
        )
        mode = result['currentMode']

        rs485_device_settings_collection.update_one(
            {"device_name": device_id},
            {"$set": {f"{mode}.minSetPoint": celsius_min_setpoint}}
        )

        return jsonify({
            "status": "Minimum setpoint updated",
            "min_setpoint": new_min_setpoint,
            "unit": unit,
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@setpoint_blueprint.route('/setpoint/min', methods=["GET"])
async def read_min_setpoint(device_id):
    """
    Read the current minimum setpoint temperature.

    This endpoint retrieves the current minimum temperature setpoint and returns it along with
    the unit that can be specified via a query parameter ('C' for Celsius or 'F' for Fahrenheit) and a timestamp.

    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Returns:
        JSON response with the current minimum setpoint value in the specified unit and a timestamp.
    """
    validate_device_id(device_id, rs485_device_collection)

    unit = request.args.get('unit', default='C', type=str).upper()  # get from query parameter
    if unit not in ['C', 'F']:
        return jsonify({"error": "Invalid unit specified. Use 'C' for Celsius or 'F' for Fahrenheit."}), 400
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument."}), 500
   
    try:
        min_setpoint_value = instrument.read_register(registeraddress=MINIMUM_SETPOINT_REGISTER, number_of_decimals=1, functioncode=3, signed=True)

        if unit == 'F':
            min_setpoint_value = celsius_to_fahrenheit(min_setpoint_value)
        
        return jsonify({
            "min_setpoint": min_setpoint_value,
            "unit": unit,
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@setpoint_blueprint.route('/setpoint/max', methods=["POST"])
async def set_max_setpoint(device_id):
    """
    Sets a new maximum setpoint temperature.

    This endpoint allows you to set a new maximum temperature setpoint. The provided maximum
    setpoint must be between 110°C (180°F) and the current maximum setpoint. The unit of the temperature
    can be specified via a query parameter ('C' for Celsius or 'F' for Fahrenheit).
    
    Path Parameter:
        device_id (str): Required. Specify which device you want the request for

    Parameters:
        - max_setpoint (float): The desired maximum temperature setpoint to be set (in the request body).
        - unit (string): The unit of the minimum setpoint ('C' or 'F') provided as a query parameter. Defaults to 'C'.

    Returns:
        - JSON response with status and new maximum setpoint value (in the specified unit), the unit, and a timestamp if successful
        - Error message if the setpoint is out of range or if the input is invalid. 
    """
    validate_device_id(device_id, rs485_device_collection)

    MAX_SETPOINT = 110                                              # Max setpoint allowed, 110 C (180 F)
    new_max_setpoint = float(request.json.get('max_setpoint'))      # get from request body
    unit = request.args.get('unit', default='C', type=str).upper()  # get from query parameter

    if new_max_setpoint is None:
        return jsonify({"error": "Maximum setpoint value is required"}), 400
    
    if unit not in ['C', 'F']:
        return jsonify({"error": "Invalid unit specified. Use 'C' for Celsius or 'F' for Fahrenheit."}), 400
     
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument"}), 500
    
    # Read current min setpoint
    try:
        min_setpoint = instrument.read_register(registeraddress=MINIMUM_SETPOINT_REGISTER, number_of_decimals=1, functioncode=3, signed=True)

        # Convert min_setpoint and MAX_SETPOINT to the same unit as the new max setpoint
        if unit == 'F':
            min_setpoint = celsius_to_fahrenheit(min_setpoint)
            MAX_SETPOINT = 180

        # Check if the new setpoint is within the allowed range
        if not (min_setpoint <= new_max_setpoint <= MAX_SETPOINT):
            return jsonify({
                "error": f"Maximum setpoint must be betweeen {min_setpoint} and {MAX_SETPOINT} {unit}."
            }), 400
        
        celsius_max_setpoint = fahrenheit_to_celsius(new_max_setpoint) if unit == 'F' else new_max_setpoint
        instrument.write_register(registeraddress=MAXIMUM_SETPOINT_REGISTER, value=float(celsius_max_setpoint), number_of_decimals=1, functioncode=6, signed=True)
        
        result = rs485_device_settings_collection.find_one(
            {"device_name": device_id},
            {"currentMode": 1, "_id": 0}
        )
        mode = result['currentMode']

        rs485_device_settings_collection.update_one(
            {"device_name": device_id},
            {"$set": {f"{mode}.maxSetPoint": celsius_max_setpoint}}
        )

        return jsonify({
                "status": "Maximum setpoint updated",
                "max_setpoint": new_max_setpoint,
                "unit": unit,
                "timestamp": get_current_timestamp()
            }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
    
@setpoint_blueprint.route('/setpoint/max', methods=["GET"])
async def read_max_setpoint(device_id):
    """
    Read the current maximum setpoint temperature.

    This endpoint retrieves the current maximum temperature setpoint and returns it along with
    the unit that can be specified via a query parameter ('C' for Celsius or 'F' for Fahrenheit) and a timestamp.

    Path Parameter:
        device_id (str): Required. Specify which device you want the request for
        
    Returns:
        JSON response with the current maximum setpoint value in the specified unit and a timestamp.
    """
    validate_device_id(device_id, rs485_device_collection)
    
    unit = request.args.get('unit', default='C', type=str).upper()  # get from query parameter
    if unit not in ['C', 'F']:
        return jsonify({"error": "Invalid unit specified. Use 'C' for Celsius or 'F' for Fahrenheit."}), 400
    
    instrument = create_instrument(device_id, rs485_device_collection)
    if instrument is None:
        return jsonify({"error": "Failed to create instrument."}), 500
   
    try:
        max_setpoint_value = instrument.read_register(registeraddress=MAXIMUM_SETPOINT_REGISTER, number_of_decimals=1, functioncode=3, signed=True)

        if unit == 'F':
            max_setpoint_value = celsius_to_fahrenheit(max_setpoint_value)
        
        return jsonify({
            "max_setpoint": max_setpoint_value,
            "unit": unit,
            "timestamp": get_current_timestamp()
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500