
from flask import Flask,g
import logging.config
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import pika

from celery import Celery
from app.decorators.restplus import api as api_rest_plus

class CalculationModuleRpcClient(object):
    def __init__(self):
        credentials = pika.PlainCredentials('admin', 'mypass')
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbit', port =5672 , credentials= credentials))

        #self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self,cm_id,data):
        self.response = None
        self.corr_id = str(cm_id)
        self.channel.basic_publish(exchange='',
                                   routing_key=constants.RPC_Q,
                                   properties=pika.BasicProperties(
                                       reply_to = self.callback_queue,
                                       correlation_id = cm_id,
                                   ),
                                   body=data)
        while self.response is None:
            self.connection.process_data_events()
        return self.response






import constants


dbGIS = SQLAlchemy()

celery = Celery(__name__, backend=constants.CELERY_RESULT_BACKEND,
                broker=constants.CELERY_BROKER_URL)



# methods
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '', 'logging.conf')
logging.config.fileConfig(log_file_path)
log = logging.getLogger(__name__)
#logging.getLogger('flask_cors').level = logging.DEBUG


def create_app(config_name):
    """
    Create app instance
    """
    app = Flask(__name__)
    cfg = os.path.join(os.getcwd(), 'config', config_name + '.py')
    app.config.from_pyfile(cfg)



    # initialize extensions
    from .api_v1 import api
    api_rest_plus.init_app(api)

    from .api_v1 import nsStats as main_stats_namespace
    api_rest_plus.add_namespace(main_stats_namespace)


    from .api_v1 import load_profile_namespace as main_heat_load_profile_namespace
    api_rest_plus.add_namespace(main_heat_load_profile_namespace)
    from .api_v1 import nsCM
    api_rest_plus.add_namespace(main_heat_load_profile_namespace)

    app.register_blueprint(api)
    dbGIS.init_app(app)

    CORS(app, resources={
        r"/api/*": {"origins": {
            "http://hotmaps.hevs.ch",
            "http://www.hotmaps.hevs.ch",
            "http://geoserver.hotmaps.hevs.ch",
            "http://www.hotmapsdev.hevs.ch",
            "http://geoserver.hotmapsdev.hevs.ch",
            "http://hotmaps.hevs.ch:8080",
            "http://hotmaps.hevs.ch:9006",
            "http://www.hotmapsdev.hevs.ch",
            "https://www.hotmapsdev.hevs.ch",
            "https://www.hotmaps.hevs.ch",
            "http://www.hotmaps.hevs.ch",
            "http://172.17.0.5/"
            "http://172.17.0.6/"
            "http://maps.googleapis.com/"
            "http://hotmaps.hevs.ch:9006",
            "http://lesly-hotmaps:4200",
            "http://albain-hotmaps:4200",
            "http://dany-hotmaps:4200",
            "http://hotmapsdev.hevs.ch",
            "http://maps.googleapis.com/maps/api/geocode/",
            "http://maps.googleapis.com/maps/api/",
            "http://maps.googleapis.com/*"
        }
        }})

    return app





#log.info(app)
