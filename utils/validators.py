# utils/validators.py
from flask import abort

AVAILABLE_DEVICES = ["device01", "device02"]

def validate_device_id(device_id):
    if device_id not in AVAILABLE_DEVICES:
        abort(404, description="Device not found")