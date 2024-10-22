from pymongo import MongoClient
from quart import Quart
from quart_cors import cors

from config import Config
from routes.cabinet import cabinet_blueprint, init_app as init_cabinet_route
from routes.compressor import compressor_blueprint, init_app as init_compressor_route
from routes.setpoint import setpoint_blueprint, init_app as init_setpoint_route
from routes.standby import standby_blueprint, init_app as init_standby_route

def create_app():
    app = Quart(__name__)
    app.config.from_object(Config)
    app = cors(app)

    # configure the MongoDB Client using the URI from the config
    client = MongoClient(app.config['MONGO_URI'])
    db = client.get_default_database()

    # Register the blueprints with the prefix '/api/v1'
    app.register_blueprint(cabinet_blueprint, url_prefix='/temperature-controller/api/v1/<device_id>')
    app.register_blueprint(compressor_blueprint, url_prefix='/temperature-controller/api/v1/<device_id>')
    app.register_blueprint(setpoint_blueprint, url_prefix='/temperature-controller/api/v1/<device_id>')
    app.register_blueprint(standby_blueprint, url_prefix='/temperature-controller/api/v1/<device_id>')

    # Initialize the collections needed for the routes
    init_cabinet_route(app, db)
    init_compressor_route(app, db)
    init_setpoint_route(app, db)
    init_standby_route(app, db)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)  # Deploy on port 5001