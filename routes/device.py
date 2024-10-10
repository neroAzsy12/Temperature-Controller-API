from flask import Blueprint, jsonify
from utils.helpers import (
    DEVICE01_CONTROLLER_SETTINGS_FILE_PATH,
    DEVICE01_CONFIG_FILE_PATH
)
from utils.validators import validate_device_id
import json

device_blueprint = Blueprint('device', __name__)

#Routes
@device_blueprint.route('/device/settings', methods=["GET"])
def get_device_settings(device_id):
    """
    Checks the device controller settings for device_id

    This endpoint retrieves the <device_id>-controller-settings.json file.

    Path parameter:
        device_id (str): Required. Specify which device you want the controller settings for

    Returns
        - JSON response with the current settings that are saved in the device
    """
    validate_device_id(device_id)

    try:
        file = open(DEVICE01_CONTROLLER_SETTINGS_FILE_PATH, 'w+')
        data = json.load(file)
        file.close()

        return jsonify(data, 200)
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@device_blueprint.route('/device/config', methods=["GET"])
def get_device_config(device_id):
    """
    Checks the device controller config for device_id

    This endpoint retrieves the <device_id>-config.json file

    Path parameter:
        device_id (str): Required. Specify which device you want the controller config for

    Returns
        - JSON response with the current config that are used to communicate with the rs485 device
    """
    validate_device_id(device_id)
    
    try:
        file = open(DEVICE01_CONFIG_FILE_PATH, 'w+')
        data = json.load(file)
        file.close()

        return jsonify(data, 200)
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500