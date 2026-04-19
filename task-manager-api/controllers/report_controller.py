from models.task import Task
from models.user import User
from models.category import Category
from database import db
from datetime import datetime, timedelta


def get_summary_report():
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    priority_counts = _get_priority_counts()

    overdue_data = _get_overdue_tasks()

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == 'done',
        Task.updated_at >= seven_days_ago
    ).count()

    user_stats = _get_user_productivity_stats()

    return {
        'generated_at': str(datetime.utcnow()),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': {
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
        },
        'tasks_by_priority': priority_counts,
        'overdue': {
            'count': overdue_data['count'],
            'tasks': overdue_data['tasks'],
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }


def get_user_report(user_id):
    user = User.query.get(user_id)
    if not user:
        return None

    tasks = Task.query.filter_by(user_id=user_id).all()

    stats = _calculate_task_statistics(tasks)

    return {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': stats
    }


def _get_priority_counts():
    return {
        'critical': Task.query.filter_by(priority=1).count(),
        'high': Task.query.filter_by(priority=2).count(),
        'medium': Task.query.filter_by(priority=3).count(),
        'low': Task.query.filter_by(priority=4).count(),
        'minimal': Task.query.filter_by(priority=5).count(),
    }


def _get_overdue_tasks():
    all_tasks = Task.query.all()
    overdue_list = []
    overdue_count = 0

    for task in all_tasks:
        if task.due_date and task.due_date < datetime.utcnow():
            if task.status not in ['done', 'cancelled']:
                overdue_count += 1
                overdue_list.append({
                    'id': task.id,
                    'title': task.title,
                    'due_date': str(task.due_date),
                    'days_overdue': (datetime.utcnow() - task.due_date).days
                })

    return {'count': overdue_count, 'tasks': overdue_list}


def _get_user_productivity_stats():
    users = User.query.all()
    user_stats = []

    for user in users:
        user_tasks = Task.query.filter_by(user_id=user.id).all()
        total = len(user_tasks)
        completed = sum(1 for t in user_tasks if t.status == 'done')

        user_stats.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': round((completed / total) * 100, 2) if total > 0 else 0
        })

    return user_stats


def _calculate_task_statistics(tasks):
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == 'done')
    pending = sum(1 for t in tasks if t.status == 'pending')
    in_progress = sum(1 for t in tasks if t.status == 'in_progress')
    cancelled = sum(1 for t in tasks if t.status == 'cancelled')
    high_priority = sum(1 for t in tasks if t.priority <= 2)

    overdue = 0
    for task in tasks:
        if task.due_date and task.due_date < datetime.utcnow():
            if task.status not in ['done', 'cancelled']:
                overdue += 1

    return {
        'total_tasks': total,
        'done': done,
        'pending': pending,
        'in_progress': in_progress,
        'cancelled': cancelled,
        'overdue': overdue,
        'high_priority': high_priority,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
    }


def get_all_categories():
    categories = Category.query.all()
    result = []
    for c in categories:
        cat_data = c.to_dict()
        cat_data['task_count'] = Task.query.filter_by(category_id=c.id).count()
        result.append(cat_data)
    return result


def create_category(name, description, color):
    category = Category()
    category.name = name
    category.description = description
    category.color = color

    db.session.add(category)
    db.session.commit()
    return category


def update_category(cat_id, **kwargs):
    category = Category.query.get(cat_id)
    if not category:
        return None

    for key, value in kwargs.items():
        setattr(category, key, value)

    db.session.commit()
    return category


def delete_category(cat_id):
    category = Category.query.get(cat_id)
    if not category:
        return False

    db.session.delete(category)
    db.session.commit()
    return True
