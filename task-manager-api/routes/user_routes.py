from flask import Blueprint, request, jsonify
from controllers import user_controller
from models.user import User
import re
import logging

user_bp = Blueprint('users', __name__)
logger = logging.getLogger(__name__)

VALID_ROLES = ['user', 'admin', 'manager']
MIN_PASSWORD_LENGTH = 4
EMAIL_REGEX = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'


@user_bp.route('/users', methods=['GET'])
def get_users():
    try:
        users = user_controller.get_all_users()
        return jsonify(users), 200
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = user_controller.get_user_with_tasks(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user), 200
    except Exception as e:
        logger.error(f"Error fetching user: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@user_bp.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Invalid data'}), 400

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')

        if not name:
            return jsonify({'error': 'Name is required'}), 400
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        if not password:
            return jsonify({'error': 'Password is required'}), 400

        if not re.match(EMAIL_REGEX, email):
            return jsonify({'error': 'Invalid email format'}), 400

        if len(password) < MIN_PASSWORD_LENGTH:
            return jsonify({'error': f'Password must be at least {MIN_PASSWORD_LENGTH} characters'}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409

        if role not in VALID_ROLES:
            return jsonify({'error': 'Invalid role'}), 400

        user = user_controller.create_user(name, email, password, role)
        return jsonify(user.to_dict()), 201
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error creating user'}), 500


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid data'}), 400

        update_data = {}

        if 'name' in data:
            update_data['name'] = data['name']

        if 'email' in data:
            if not re.match(EMAIL_REGEX, data['email']):
                return jsonify({'error': 'Invalid email format'}), 400
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                return jsonify({'error': 'Email already registered'}), 409
            update_data['email'] = data['email']

        if 'password' in data:
            if len(data['password']) < MIN_PASSWORD_LENGTH:
                return jsonify({'error': f'Password must be at least {MIN_PASSWORD_LENGTH} characters'}), 400
            update_data['password'] = data['password']

        if 'role' in data:
            if data['role'] not in VALID_ROLES:
                return jsonify({'error': 'Invalid role'}), 400
            update_data['role'] = data['role']

        if 'active' in data:
            update_data['active'] = data['active']

        updated_user = user_controller.update_user(user_id, **update_data)
        return jsonify(updated_user.to_dict()), 200
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error updating user'}), 500


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        if not user_controller.delete_user(user_id):
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error deleting user'}), 500


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    try:
        tasks = user_controller.get_user_tasks(user_id)
        if tasks is None:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(tasks), 200
    except Exception as e:
        logger.error(f"Error fetching user tasks: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@user_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid data'}), 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        user = user_controller.authenticate_user(email, password)
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'token': 'fake-jwt-token-' + str(user.id)
        }), 200
    except Exception as e:
        logger.error(f"Error during login: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
