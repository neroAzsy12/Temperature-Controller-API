from flask import Blueprint, jsonify
from utils.helpers import (
    DEVICE01_CONTROLLER_SETTINGS_FILE_PATH,
    DEVICE01_CONFIG_FILE_PATH
)
from utils.validators import validate_device_id
import json

device_blueprint = Blueprint('device', __name__)
rs485_device_collection = None
rs485_device_settings_collection = None

def init_app(app, db):
    global rs485_device_collection
    global rs485_device_settings_collection
    rs485_device_collection = db['rs485_devices']
    rs485_device_settings_collection = db['rs485_device_controller_settings']

#Routes
@device_blueprint.route('/device/config', methods=["GET"])
def get_device_settings(device_id):
    """
    Checks the device controller settings for device_id

    This endpoint retrieves the <device_id>-controller-settings.json file.

    Path parameter:
        device_id (str): Required. Specify which device you want the controller settings for

    Returns
        - JSON response with the current settings that are saved in the device
    """
    validate_device_id(device_id, rs485_device_collection)

    try:
        device = rs485_device_collection.find_one({"device_name": device_id}, {"_id": 0})
        return jsonify(device), 200
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@device_blueprint.route('/device/settings', methods=["GET"])
def get_device_config(device_id):
    """
    Checks the device controller config for device_id

    This endpoint retrieves the <device_id>-config.json file

    Path parameter:
        device_id (str): Required. Specify which device you want the controller config for

    Returns
        - JSON response with the current config that are used to communicate with the rs485 device
    """
    validate_device_id(device_id, rs485_device_collection)
    
    try:
        device_settings = rs485_device_settings_collection.find_one({"device_name": device_id}, {"_id": 0})
        return jsonify(device_settings), 200
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500