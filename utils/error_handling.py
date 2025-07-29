import functools
import logging
from flask import jsonify
from pymongo.errors import ConnectionFailure, PyMongoError

logger = logging.getLogger('todo_api')

def handle_db_errors(func):
    """Decorator to handle common database and ID-related exceptions."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConnectionFailure as e:
            logger.error(f'MongoDB connection error in {func.__name__}: {str(e)}', exc_info=True)
            return jsonify({'error': 'Database connection error'}), 500
        except PyMongoError as e:
            logger.error(f'MongoDB operation error in {func.__name__}: {str(e)}', exc_info=True)
            return jsonify({'error': 'Database operation failed'}), 500
        except ValueError as e:
            task_id = kwargs.get('task_id', 'unknown')
            logger.warning(f'Invalid task ID {task_id} in {func.__name__}: {str(e)}')
            return jsonify({'error': 'Invalid task ID'}), 400
        except Exception as e:
            logger.error(f'Unexpected error in {func.__name__}: {str(e)}', exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500
    return wrapper