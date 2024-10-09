from flask import Blueprint, jsonify, request
from utils.helpers import (
    create_instrument,
    get_current_timestamp
)
from utils.validators import (
    validate_device_id
)

convert_blueprint = Blueprint('convert', __name__)

"""
Process for Cooler to Freezer

TBD:
- Figure out how to determine the current state of the cold cabinet 
    - Cooler Mode
    - Freezer Mode

- Register 209, Defrost Start Mode (NON, TIM, FRO, RTC) maybe use it?

1. Check status of manual standby button
- if enabled, disable it
- if disabled, proceed

2. 
"""