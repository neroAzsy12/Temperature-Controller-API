from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient
from routes.compressor import compressor_blueprint, init_app as init_compressor
from routes.device import device_blueprint, init_app as init_device
from routes.probe import probe_blueprint, init_app as init_probe
from routes.setpoint import setpoint_blueprint, init_app as init_setpoint
from routes.standby import standby_blueprint, init_app as init_standby
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # Load configuration
    CORS(app)

    # configure the MongoDB Client using the URI from the config
    client = MongoClient(app.config['MONGO_URI'])
    db = client.get_default_database()  # Automatically use the specified database

    # Register the probe blueprint with the '/api/v1'
    app.register_blueprint(compressor_blueprint, url_prefix='/temperature-controller/api/v1/<device_id>')
    app.register_blueprint(device_blueprint, url_prefix='/temperature-controller/api/v1/<device_id>')
    app.register_blueprint(probe_blueprint, url_prefix='/temperature-controller/api/v1/<device_id>')
    app.register_blueprint(setpoint_blueprint, url_prefix='/temperature-controller/api/v1/<device_id>')
    app.register_blueprint(standby_blueprint, url_prefix='/temperature-controller/api/v1/<device_id>')

    # Initialize the collections needed for the routes
    init_compressor(app, db)
    init_device(app, db)
    init_probe(app, db)
    init_setpoint(app, db)
    init_standby(app, db)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)  # Deploy on port 5001