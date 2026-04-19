from flask import Blueprint, request, jsonify
from controllers import report_controller
import logging

report_bp = Blueprint('reports', __name__)
logger = logging.getLogger(__name__)

DEFAULT_COLOR = '#000000'


@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    try:
        report = report_controller.get_summary_report()
        return jsonify(report), 200
    except Exception as e:
        logger.error(f"Error generating summary report: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error generating report'}), 500


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    try:
        report = report_controller.get_user_report(user_id)
        if not report:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(report), 200
    except Exception as e:
        logger.error(f"Error generating user report: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error generating report'}), 500


@report_bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = report_controller.get_all_categories()
        return jsonify(categories), 200
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@report_bp.route('/categories', methods=['POST'])
def create_category():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid data'}), 400

        name = data.get('name')
        if not name:
            return jsonify({'error': 'Name is required'}), 400

        description = data.get('description', '')
        color = data.get('color', DEFAULT_COLOR)

        category = report_controller.create_category(name, description, color)
        return jsonify(category.to_dict()), 201
    except Exception as e:
        logger.error(f"Error creating category: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error creating category'}), 500


@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    try:
        data = request.get_json()
        update_data = {}

        if 'name' in data:
            update_data['name'] = data['name']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'color' in data:
            update_data['color'] = data['color']

        category = report_controller.update_category(cat_id, **update_data)
        if not category:
            return jsonify({'error': 'Category not found'}), 404

        return jsonify(category.to_dict()), 200
    except Exception as e:
        logger.error(f"Error updating category: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error updating category'}), 500


@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    try:
        if not report_controller.delete_category(cat_id):
            return jsonify({'error': 'Category not found'}), 404
        return jsonify({'message': 'Category deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting category: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error deleting category'}), 500
