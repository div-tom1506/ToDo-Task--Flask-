from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest, NotFound
from bson import ObjectId
from models.task import Task
import logging
import datetime

task_bp = Blueprint('task', __name__)
logger = logging.getLogger('todo_api')

class ValidationError(Exception):
    pass

@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        logger.info('Fetching all tasks')
        tasks = current_app.db.tasks.find()
        return jsonify([Task.from_dict(task).to_dict() for task in tasks]), 200
    except Exception as e:
        logger.error(f'Error fetching tasks: {str(e)}', exc_info=True)

@task_bp.route('/tasks', methods=['POST'])
def create_task():
    try:
        data = request.get_json()
        if not data or 'title' not in data:
            logger.warning('Invalid request: title is required')
            raise ValidationError('Title is required')
