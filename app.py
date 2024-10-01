from flask import Flask
from flask_cors import CORS
from routes.compressor import compressor_blueprint
from routes.probe import probe_blueprint
from routes.setpoint import setpoint_blueprint

def create_app():
    app = Flask(__name__)

    CORS(app)

    # Register the probe blueprint with the '/api/v1'
    app.register_blueprint(compressor_blueprint, url_prefix='/temperature-controller/api/v1/<device_id>')
    app.register_blueprint(probe_blueprint, url_prefix='/temperature-controller/api/v1/<device_id>')
    app.register_blueprint(setpoint_blueprint, url_prefix='/temperature-controller/api/v1/<device_id>')

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5001)  # Deploy on port 5001
