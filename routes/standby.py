from flask import Blueprint, jsonify, request
from utils.helpers import (
    create_instrument,
    get_current_timestamp
)
from utils.validators import (
    validate_device_id
)

standby_blueprint = Blueprint("standby", __name__, url_prefix='/standby')

STANDBY_REGISTER = 700          # Register for Standby (set on/off for standby)
MANUAL_STANDBY_REGISTER = 701   # Register for Manual Standby (enable/disable the power button on display)

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
    validate_device_id(device_id)

    instrument = create_instrument()
    if instrument is None:
        return jsonify({
            "error": "Failed to create instrument"
        }), 500
    
@standby_blueprint.route('/status/manual', methods = ["GET"])
def get_manual_standby_status(device_id):
    """
    Gets the status of the manual standby mode from the temperature controller display

    This endpoint checks status of standby mode from the temperature controller display
    """    
