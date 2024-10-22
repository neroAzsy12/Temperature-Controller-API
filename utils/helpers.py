from datetime import datetime
from tzlocal import get_localzone
import math
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
    return math.ceil(fahrenheit)

def fahrenheit_to_celsius(fahrenheit):
    """Convert Fahrenheit to Celsius and round to the nearest tenth."""
    celsius = (fahrenheit - 32) / 1.8
    return round(celsius, 1) # Round to the nearest tenth

def create_instrument(device, device_collection):
    """ Create and return a MinimalModBus instrument instance. """
    try:
        device_config = device_collection.find_one({"device_name": device})

        client = minimalmodbus.Instrument(port=device_config["port"], slaveaddress=device_config["slaveAddress"])

        # Set the minimalmodbus instrument mode (ASCII or RTU)
        if device_config["mode"] == "ASCII":
            client.mode = minimalmodbus.MODE_ASCII
        else:
            client.mode = minimalmodbus.MODE_RTU    

        # Set the Bit Parity ('E'ven, 'O'dd, 'N'one)
        if device_config["parity"] == 'E':
            client.serial.parity = minimalmodbus.serial.PARITY_EVEN
        elif device_config["parity"] == 'O':
            client.serial.parity = minimalmodbus.serial.PARITY_ODD
        elif device_config["parity"] == 'N':
            client.serial.parity = minimalmodbus.serial.PARITY_NONE
        else:
            client.serial.parity = minimalmodbus.serial.PARITY_MARK
        
        client.serial.baudrate = device_config["baudrate"]
        client.serial.bytesize = device_config["bytesize"]
        client.serial.stopbits = device_config["stopbits"]
        client.serial.timeout = device_config["timeout"]

        client.close_port_after_each_call = True 
        client.clear_buffers_before_each_transaction = True

        # Test the connection
        client.read_register(199)
        return client
    except Exception as e:
        print(f"Error creating instrument: {e}")
        return None