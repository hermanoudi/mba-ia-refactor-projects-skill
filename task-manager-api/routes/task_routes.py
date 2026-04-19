from flask import Blueprint, request, jsonify
from controllers import task_controller
from models.user import User
from models.category import Category
from datetime import datetime
import logging

task_bp = Blueprint('tasks', __name__)
logger = logging.getLogger(__name__)

VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PRIORITY = 1
MAX_PRIORITY = 5


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        tasks = task_controller.get_all_tasks_with_details()
        return jsonify(tasks), 200
    except Exception as e:
        logger.error(f"Error fetching tasks: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = task_controller.get_task_by_id(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Invalid data'}), 400

        title = data.get('title')
        if not title:
            return jsonify({'error': 'Title is required'}), 400

        if len(title) < MIN_TITLE_LENGTH:
            return jsonify({'error': f'Title must be at least {MIN_TITLE_LENGTH} characters'}), 400

        if len(title) > MAX_TITLE_LENGTH:
            return jsonify({'error': f'Title must not exceed {MAX_TITLE_LENGTH} characters'}), 400

        description = data.get('description', '')
        status = data.get('status', 'pending')
        priority = data.get('priority', 3)
        user_id = data.get('user_id')
        category_id = data.get('category_id')
        due_date = data.get('due_date')
        tags = data.get('tags')

        if status not in VALID_STATUSES:
            return jsonify({'error': 'Invalid status'}), 400

        if not isinstance(priority, int) or priority < MIN_PRIORITY or priority > MAX_PRIORITY:
            return jsonify({'error': f'Priority must be between {MIN_PRIORITY} and {MAX_PRIORITY}'}), 400

        if user_id and not User.query.get(user_id):
            return jsonify({'error': 'User not found'}), 404

        if category_id and not Category.query.get(category_id):
            return jsonify({'error': 'Category not found'}), 404

        parsed_due_date = None
        if due_date:
            try:
                parsed_due_date = datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        task = task_controller.create_task(
            title=title,
            description=description,
            status=status,
            priority=priority,
            user_id=user_id,
            category_id=category_id,
            due_date=parsed_due_date,
            tags=tags
        )

        return jsonify(task.to_dict()), 201
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error creating task'}), 500


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    try:
        task = task_controller.get_task_by_id(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid data'}), 400

        update_data = {}

        if 'title' in data:
            if len(data['title']) < MIN_TITLE_LENGTH:
                return jsonify({'error': f'Title must be at least {MIN_TITLE_LENGTH} characters'}), 400
            if len(data['title']) > MAX_TITLE_LENGTH:
                return jsonify({'error': f'Title must not exceed {MAX_TITLE_LENGTH} characters'}), 400
            update_data['title'] = data['title']

        if 'description' in data:
            update_data['description'] = data['description']

        if 'status' in data:
            if data['status'] not in VALID_STATUSES:
                return jsonify({'error': 'Invalid status'}), 400
            update_data['status'] = data['status']

        if 'priority' in data:
            if not isinstance(data['priority'], int) or data['priority'] < MIN_PRIORITY or data['priority'] > MAX_PRIORITY:
                return jsonify({'error': f'Priority must be between {MIN_PRIORITY} and {MAX_PRIORITY}'}), 400
            update_data['priority'] = data['priority']

        if 'user_id' in data:
            if data['user_id'] and not User.query.get(data['user_id']):
                return jsonify({'error': 'User not found'}), 404
            update_data['user_id'] = data['user_id']

        if 'category_id' in data:
            if data['category_id'] and not Category.query.get(data['category_id']):
                return jsonify({'error': 'Category not found'}), 404
            update_data['category_id'] = data['category_id']

        if 'due_date' in data:
            if data['due_date']:
                try:
                    update_data['due_date'] = datetime.strptime(data['due_date'], '%Y-%m-%d')
                except ValueError:
                    return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
            else:
                update_data['due_date'] = None

        if 'tags' in data:
            update_data['tags'] = data['tags']

        updated_task = task_controller.update_task(task_id, **update_data)
        return jsonify(updated_task.to_dict()), 200
    except Exception as e:
        logger.error(f"Error updating task: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error updating task'}), 500


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        if not task_controller.delete_task(task_id):
            return jsonify({'error': 'Task not found'}), 404
        return jsonify({'message': 'Task deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error deleting task'}), 500


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    try:
        query = request.args.get('q', '')
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')
        user_id = request.args.get('user_id', '')

        results = task_controller.search_tasks(
            query=query,
            status=status,
            priority=priority,
            user_id=user_id
        )

        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Error searching tasks: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error searching tasks'}), 500


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    try:
        stats = task_controller.get_task_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error fetching task stats: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error fetching statistics'}), 500
