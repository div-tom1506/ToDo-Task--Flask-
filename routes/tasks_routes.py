from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest, NotFound
from models.task import Task
import logging
from datetime import datetime, timezone
from utils.error_handling import handle_db_errors

tasks_bp = Blueprint('task', __name__)
logger = logging.getLogger('todo_api')

class ValidationError(Exception):
    pass

@tasks_bp.route('/tasks', methods=['GET'])
@handle_db_errors
def get_tasks():
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

@tasks_bp.route('/tasks', methods=['POST'])
@handle_db_errors
def create_task():
    data = request.get_json()
    if not data or 'title' not in data:
        logger.warning('Invalid request: title is required')
        return jsonify({'error': 'Title is required'}), 400
        
    task = Task(data['title'], data.get('description', ''))
    current_app.db.tasks.insert_one(task.to_dict())
    logger.info(f'Created task with ID: {task.id}')
    return jsonify(task.to_dict()), 201

@tasks_bp.route('/tasks/<task_id>', methods=['GET'])
@handle_db_errors
def get_task(task_id):
    # if id is stored as object in db
    # task = current_app.db.tasks.find_one({'_id': ObjectId(task_id)}) 
    task = current_app.db.tasks.find_one({'_id': task_id})  # if string _id
    if not task:
        logger.warning(f'Task not found: {task_id}')
        return jsonify({'error': 'Task not found'}), 404
        
    logger.info(f'Retrieved task: {task_id}')
    return jsonify(Task.from_dict(task).to_dict()), 200

@tasks_bp.route('/tasks/<task_id>', methods=['PUT'])
@handle_db_errors
def update_task(task_id):
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

@tasks_bp.route('/tasks/<task_id>', methods=['DELETE'])
@handle_db_errors
def delete_task(task_id):
    result = current_app.db.tasks.delete_one({'_id': task_id})
    if result.deleted_count == 0:
        logger.warning(f'Task not found for deletion: {task_id}')
        return jsonify({'error': 'Task not found'}), 404
    logger.info(f'Deleted task: {task_id}')
    return jsonify({'message': 'Task deleted'}), 200
