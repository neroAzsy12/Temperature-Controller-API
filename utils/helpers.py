from datetime import datetime
from tzlocal import get_localzone
import minimalmodbus

def get_current_timestamp():
    """Returns a timestamp in the form 'YYYY-MM-DDThh:mm:ssTZD'"""
    # Get the local timezone
    local_tz = get_localzone()
    current_time = datetime.now(local_tz)

    # Format the timestamp
    formatted_timestamp = current_time.strftime('%Y-%m-%dT%H:%M:%S')

    # Get the UTC offset
    tz_offset = current_time.strftime('%z')
    formatted_timestamp += f'{tz_offset[:3]}:{tz_offset[3:]}'  # Add colon in offset format

    return formatted_timestamp

def celsius_to_fahrenheit(celsius):
    """Convert Celsius to Fahrenheit and round to the nearest whole number."""
    fahrenheit = (celsius * 1.8) + 32
    return round(fahrenheit)

def fahrenheit_to_celsius(fahrenheit):
    """Convert Fahrenheit to Celsius and round to the nearest tenth."""
    celsius = (fahrenheit - 32) / 1.8
    return round(celsius, 1) # Round to the nearest tenth

CONTROLLER_CONFIG = {
    "lae-controller": {
        "mode": minimalmodbus.MODE_ASCII,
        "baudrate": 9600,
        "bytesize": 7,
        "parity": minimalmodbus.serial.PARITY_EVEN,
        "stopbits": 1,
        "timeout": 3
    }
}

DEVICE_CONFIG = {
    "device01": {
        "type": "lae_controller",
        "port": "COM5",
        "address": 1
    }
}

def create_instrument(device="device01"):
    """Create and return a MinimalModbus instrument instance."""
    try:
        device_config = DEVICE_CONFIG[device]
        device_type = CONTROLLER_CONFIG[device_config["type"]]
        
        client = minimalmodbus.Instrument(device_config["port"], slaveaddress=device_config["address"])
        client.mode = device_type["mode"]
        client.serial.baudrate = device_type["baudrate"]
        client.serial.bytesize = device_type["bytesize"]
        client.serial.parity = device_type["parity"]
        client.serial.stopbits = device_type["stopbits"]
        client.serial.timeout = device_type["timeout"]

        client.close_port_after_each_call = True 
        client.clear_buffers_before_each_transaction = True

        # Test the connection
        client.read_register(199)
        return client
    
    except Exception as e:
        print(f"Error creating instrument: {e}")
        return None