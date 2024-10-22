from quart import abort

def validate_device_id(device_id, device_collection):
    device = device_collection.find_one({'device_name': device_id})

    if device is None:
        abort(404, description='Device was not found')