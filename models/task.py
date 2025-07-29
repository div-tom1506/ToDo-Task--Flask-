import logging
from bson import ObjectId
from datetime import datetime, timezone

logger = logging.getLogger('todo_app')

class Task:
    def __init__(self, title, description=''):
        try:
            # Input validation
            if not isinstance(title, str) or not title.strip():
                raise ValueError('Title must be a not be empty')
            
            self.id = str(ObjectId())
            self.title = title.strip()
            self.description = description.strip() if isinstance(description, str) else ''
            self.completed = False
            self.created_at = datetime.now(timezone.utc)
            self.updated_at = self.created_at
            logger.debug(f'Initialized task: {self.id}')
        except Exception as e:
            logger.error(f'Error initializing task: {str(e)}', exc_info=True)
            raise

        def to_dict(self):
            return {
                '_id': ObjectId(self.id),
                'title': self.title,
                'description': self.description,
                'completed': self.completed,
                'created_at': self.created_at,
                'updated_at': self.updated_at
            }
        
        @classmethod
        def from_dict(cls, data):
            try:
                task = (data['title'], data.get('description', ''))
                task.id = str(data['_id'])
                task.completed = data.get('completed', False)
                task.created_at = data.get('created_at', datetime.now(timezone.utc))
                task.updated_at = data.get('updated_at', task.created_at)
                logger.debug(f'Created task object from dict: {task.id}')
                return task
            except Exception as e:
                logger.error(f'Error creating task from dict: {str(e)}', exc_info=True)
            raise