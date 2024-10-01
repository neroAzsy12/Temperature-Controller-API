# utils/validators.py
from flask import abort

valid_device_ids = ["device01", "device02"]

def validate_device_id(device_id):
    if device_id not in valid_device_ids:
        abort(404, description="Device not found")