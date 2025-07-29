from flask import jsonify
from werkzeug.exceptions import NotFound, BadRequest
import logging

logger = logging.getLogger('todo_api')

# Global exception handling
def register_exception_handlers(app):
    @app.errorhandler(NotFound)
    def handle_not_found(error):
        logger.warning(f'Not found error: {str(error)}')
        return jsonify({'error': str(error) or 'Resource not found'}), 404

    @app.errorhandler(BadRequest)
    def handle_bad_request(error):
        logger.warning(f'Bad request error: {str(error)}')
        return jsonify({'error': str(error) or 'Bad request'}), 400

    @app.errorhandler(Exception)
    def handle_error(error):
        logger.error(f'Unhandled error: {str(error)}', exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500