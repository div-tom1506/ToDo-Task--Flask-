from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest, NotFound
from bson import ObjectId
from models.task import Task
import logging
import datetime

tasks_bp = Blueprint('task', __name__)
logger = logging.getLogger('todo_api')

class ValidationError(Exception):
    pass

@tasks_bp.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        logger.info('Fetching all tasks')
        tasks = current_app.db.tasks.find()
        return jsonify([Task.from_dict(task).to_dict() for task in tasks]), 200
    except Exception as e:
        logger.error(f'Error fetching tasks: {str(e)}', exc_info=True)

@tasks_bp.route('/tasks', methods=['POST'])
def create_task():
    try:
        data = request.get_json()
        if not data or 'title' not in data:
            logger.warning('Invalid request: title is required')
            raise ValidationError('Title is required')
        
        task = Task(data['title'], data.get('description', ''))
        current_app.db.tasks.insert_one(task.to_dict())
        logger.info(f'Created task with ID: {task.id}')
        return jsonify(task.to_dict()), 201
    
    except ValidationError as e:
        logger.warning(f'Validation error: {str(e)}')
        raise BadRequest(str(e))
    except Exception as e:
        logger.error(f'Error creating task: {str(e)}', exc_info=True)
        raise

@tasks_bp.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    try:
        task = current_app.db.tasks.find_one({'_id': ObjectId(task_id)})
        if not task:
            logger.warning(f'Task not found: {task_id}')
            raise NotFound('Task not found')
        logger.info(f'Retrieved task: {task_id}')
        return jsonify(Task.from_dict(task).to_dict()), 200
    
    except NotFound as e:
        raise
    except Exception as e:
        logger.error(f'Error retrieving task {task_id}: {str(e)}', exc_info=True)
        raise

@tasks_bp.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    try:
        task = current_app.db.tasks.find_one({'_id': ObjectId(task_id)})
        if not task:
            logger.warning(f'Task not found for update: {task_id}')
            raise NotFound('Task not found')
        
        data = request.get_json()
        if not data:
            logger.warning('Invalid update request: no data provided')
            raise ValidationError('No data provided')
        
        update_data = {}

        if 'title' in data:
            if not isinstance(data['title'], str) or not data['title'].strip():
                logger.warning('Invalid update request: title must be a non-empty string')
                raise ValidationError('Title must be a non-empty string')
            update_data['title'] = data['title'].strip()
        
        if 'description' in data:
            update_data['description'] = data['description'].strip() if isinstance(data['description'], str) else ''
        
        if 'completed' in data:
            update_data['completed'] = data['completed']
        
        update_data['updated_at'] = datetime.utcnow()

        if update_data:
            current_app.db.tasks.update_one(
                {'_id': ObjectId(task_id)},
                {'$set': update_data}
            )
            updated_task = current_app.db.tasks.find_one({'_id': ObjectId(task_id)})
            logger.info(f'Updated task: {task_id}')
            return jsonify(Task.from_dict(update_data).to_dict()), 200
        else:
            logger.warning('No valid fields provided for update')
            raise ValidationError('No valid fields provided for update')
        
    except (NotFound, ValidationError) as e:
        raise
    except Exception as e:
        logger.error(f'Error updating task {task_id}: {str(e)}', exc_info=True)
        raise

@tasks_bp.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        result = current_app.db.tasks.delete_one({'_id': ObjectId(task_id)})
        if result.deleted_count == 0:
            logger.warning(f'Task not found for deletion: {task_id}')
            raise NotFound('Task not found')
        logger.info(f'Deleted task: {task_id}')
        return jsonify({'message': 'Task deleted'}), 200
    
    except NotFound as e:
        raise
    except Exception as e:
        logger.error(f'Error deleting task {task_id}: {str(e)}', exc_info=True)
        raise
