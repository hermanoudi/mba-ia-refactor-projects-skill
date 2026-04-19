from models.user import User
from models.task import Task
from database import db


def get_all_users():
    users = User.query.all()
    result = []
    for u in users:
        user_data = {
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'role': u.role,
            'active': u.active,
            'created_at': str(u.created_at),
            'task_count': len(u.tasks)
        }
        result.append(user_data)
    return result


def get_user_with_tasks(user_id):
    user = User.query.get(user_id)
    if not user:
        return None

    data = user.to_dict()
    tasks = Task.query.filter_by(user_id=user_id).all()
    data['tasks'] = [t.to_dict() for t in tasks]
    return data


def create_user(name, email, password, role):
    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role

    db.session.add(user)
    db.session.commit()
    return user


def update_user(user_id, **kwargs):
    user = User.query.get(user_id)
    if not user:
        return None

    for key, value in kwargs.items():
        if key == 'password':
            user.set_password(value)
        else:
            setattr(user, key, value)

    db.session.commit()
    return user


def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return False

    tasks = Task.query.filter_by(user_id=user_id).all()
    for task in tasks:
        db.session.delete(task)

    db.session.delete(user)
    db.session.commit()
    return True


def get_user_tasks(user_id):
    user = User.query.get(user_id)
    if not user:
        return None

    tasks = Task.query.filter_by(user_id=user_id).all()
    result = []
    for task in tasks:
        task_data = task.to_dict()
        task_data['overdue'] = _is_task_overdue(task)
        result.append(task_data)

    return result


def _is_task_overdue(task):
    from datetime import datetime
    if not task.due_date:
        return False
    if task.due_date < datetime.utcnow():
        return task.status not in ['done', 'cancelled']
    return False


def authenticate_user(email, password):
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return None
    if not user.active:
        return None
    return user
