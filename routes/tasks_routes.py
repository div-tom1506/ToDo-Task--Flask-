from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest, NotFound
from models.task import Task
import logging
from datetime import datetime, timezone
from pymongo.errors import PyMongoError, ConnectionFailure

tasks_bp = Blueprint('task', __name__)
logger = logging.getLogger('todo_api')

class ValidationError(Exception):
    pass

@tasks_bp.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        logger.info('Fetching all tasks')
        tasks = current_app.db.tasks.find()
        task_list = []
        for task in tasks:
            try:
                task_list.append(Task.from_dict(task).to_dict())
            except Exception as e:
                logger.warning(f'Failed to process task {task.get("_id")}: {str(e)}')
                continue
        if not task_list:
            logger.info('No valid tasks found')
        return jsonify(task_list), 200
    
    except ConnectionFailure as e:
        logger.error(f'MongoDB connection error: {str(e)}', exc_info=True)
        return jsonify({'error': 'Database connection error'}), 500
    except PyMongoError as e:
        logger.error(f'MongoDB operation error: {str(e)}', exc_info=True)
        return jsonify({'error': 'Database operation failed'}), 500
    except Exception as e:
        logger.error(f'Unexpected error fetching tasks: {str(e)}', exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@tasks_bp.route('/tasks', methods=['POST'])
def create_task():
    try:
        data = request.get_json()
        if not data or 'title' not in data:
            logger.warning('Invalid request: title is required')
            return jsonify({'error': 'Title is required'}), 400
        
        task = Task(data['title'], data.get('description', ''))
        current_app.db.tasks.insert_one(task.to_dict())
        logger.info(f'Created task with ID: {task.id}')
        return jsonify(task.to_dict()), 201
    
    except ConnectionError as e:
        logger.error(f'MongoDB connection error: {str(e)}', exc_info=True)
        return jsonify({'error': 'Database connection error'}), 500
    except PyMongoError as e:
        logger.error(f'MongoDB operation error: {str(e)}', exc_info=True)
        return jsonify({'error': 'Database operation failed'}), 500
    except Exception as e:
        logger.error(f'Error creating task: {str(e)}', exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@tasks_bp.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    try:
        # if id is stored as object in db
        # task = current_app.db.tasks.find_one({'_id': ObjectId(task_id)}) 
        task = current_app.db.tasks.find_one({'_id': task_id})  # if string _id
        if not task:
            logger.warning(f'Task not found: {task_id}')
            return jsonify({'error': 'Task not found'}), 404
        
        logger.info(f'Retrieved task: {task_id}')
        return jsonify(Task.from_dict(task).to_dict()), 200
    
    except ValueError as e:
        logger.warning(f'Invalid task ID {task_id}: {str(e)}')
        return jsonify({'error': 'Invalid task ID'}), 400
    except ConnectionError as e:
        logger.error(f'MongoDB connection error: {str(e)}', exc_info=True)
        return jsonify({'error': 'Database connection error'}), 500
    except PyMongoError as e:
        logger.error(f'MongoDB operation error: {str(e)}', exc_info=True)
        return jsonify({'error': 'Database operation failed'}), 500
    except Exception as e:
        logger.error(f'Error retrieving task {task_id}: {str(e)}', exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@tasks_bp.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    try:
        task = current_app.db.tasks.find_one({'_id': task_id})
        if not task:
            logger.warning(f'Task not found for update: {task_id}')
            return jsonify({'error': 'Task not found'}), 404
        
        data = request.get_json()
        if not data:
            logger.warning('Invalid update request: no data provided')
            return jsonify({'error': 'No data provided'}), 400
        
        update_data = {}

        if 'title' in data:
            if not isinstance(data['title'], str) or not data['title'].strip():
                logger.warning('Invalid update request: title must be a non-empty string')
                return jsonify({'error': 'Title must be a non-empty string'}), 400
            update_data['title'] = data['title'].strip()
        
        if 'description' in data:
            update_data['description'] = data['description'].strip() if isinstance(data['description'], str) else ''
        
        if 'completed' in data:
            update_data['completed'] = data['completed']
        
        update_data['updated_at'] = datetime.now(timezone.utc)

        if update_data:
            current_app.db.tasks.update_one(
                {'_id': task_id},
                {'$set': update_data}
            )
            updated_task = task = current_app.db.tasks.find_one({'_id': task_id})
            logger.info(f'Updated task: {task_id}')
            return jsonify(Task.from_dict(updated_task).to_dict()), 200
        else:
            logger.warning('No valid fields provided for update')
            return jsonify({'error': 'No valid fields provided for update'}), 400
        
    except ValueError as e:
        logger.warning(f'Invalid task ID {task_id}: {str(e)}')
        return jsonify({'error': 'Invalid task ID'}), 400
    except ConnectionError as e:
        logger.error(f'MongoDB connection error: {str(e)}', exc_info=True)
        return jsonify({'error': 'Database connection error'}), 500
    except PyMongoError as e:
        logger.error(f'MongoDB operation error: {str(e)}', exc_info=True)
        return jsonify({'error': 'Database operation failed'}), 500
    except Exception as e:
        logger.error(f'Error updating task {task_id}: {str(e)}', exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@tasks_bp.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        result = current_app.db.tasks.delete_one({'_id': task_id})
        if result.deleted_count == 0:
            logger.warning(f'Task not found for deletion: {task_id}')
            return jsonify({'error': 'Task not found'}), 404
        logger.info(f'Deleted task: {task_id}')
        return jsonify({'message': 'Task deleted'}), 200
    
    except ValueError as e:
        logger.warning(f'Invalid task ID {task_id}: {str(e)}')
        return jsonify({'error': 'Invalid task ID'}), 400
    except ConnectionError as e:
        logger.error(f'MongoDB connection error: {str(e)}', exc_info=True)
        return jsonify({'error': 'Database connection error'}), 500
    except PyMongoError as e:
        logger.error(f'MongoDB operation error: {str(e)}', exc_info=True)
        return jsonify({'error': 'Database operation failed'}), 500
    except Exception as e:
        logger.error(f'Error deleting task {task_id}: {str(e)}', exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
