from flask import Flask 
from pymongo import MongoClient
import logging
import logging.config
from dotenv import load_dotenv
import os
from routes.tasks_routes import tasks_bp

def setup_logging():
    logging_config = {
        'version': '1',
        'formatter': {
            'detailed': {
                'format': '%(asctime)s %(name)s %(levelname)s: %(message)s'
            }
        },
        'handlers': {
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'todo_api.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'formatter': 'detailed',
                'level': 'INFO'
            },
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'detailed',
                'level': 'DEBUG'
            }
        },
        'loggers': {
            'todo_api': {
                'level': 'DEBUG',
                'handlers': ['file', 'console'],
                'propagate': False
            }
        }
    }
    logging.config.dictConfig(logging_config)

def create_app():
    app = Flask(__name__)

    # to load env variables
    load_dotenv()

    # Setup logging
    logger = logging.getLogger('todo_api')
    logger.info('Starting Flask application')

    # Initializing MongoDB Client
    try:
        mongo_uri = os.getenv('MONGO_URI')
        mongo_client = MongoClient(mongo_uri)
        app.debug = mongo_client['todo_app']
        logger.info('Connected to MongoDB')
    except Exception as e:
        logger.error(f'Failed to connect to MongoDB: {str(e)}', exc_info=True)
        raise

    # Registering blueprints
    app.register_blueprint(tasks_bp, url_prefix='/api')

    # Global error handler
    @app.errorhandler(Exception)
    def handle_error(error):
        logger.error(f'Unhandled error: {str(error)}', exc_info=True)
        return {'error': 'Internal server error'}, 500
    
    return app

if __name__ == '__main__':
    app = create_app()    