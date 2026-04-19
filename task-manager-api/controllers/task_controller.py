from models.task import Task
from models.user import User
from models.category import Category
from database import db
from datetime import datetime


def get_all_tasks_with_details():
    tasks = Task.query.options(
        db.joinedload(Task.user),
        db.joinedload(Task.category)
    ).all()
    return [_enrich_task(t) for t in tasks]


def get_task_by_id(task_id):
    task = Task.query.get(task_id)
    if not task:
        return None
    return _enrich_task(task)


def _enrich_task(task):
    data = task.to_dict()
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    data['overdue'] = _is_overdue(task)
    return data


def _is_overdue(task):
    if not task.due_date:
        return False
    if task.due_date < datetime.utcnow():
        return task.status not in ['done', 'cancelled']
    return False


def create_task(title, description, status, priority, user_id, category_id, due_date, tags):
    task = Task()
    task.title = title
    task.description = description
    task.status = status
    task.priority = priority
    task.user_id = user_id
    task.category_id = category_id

    if due_date:
        task.due_date = due_date

    if tags:
        if isinstance(tags, list):
            task.tags = ','.join(tags)
        else:
            task.tags = tags

    db.session.add(task)
    db.session.commit()
    return task


def update_task(task_id, **kwargs):
    task = Task.query.get(task_id)
    if not task:
        return None

    for key, value in kwargs.items():
        if key == 'tags' and value:
            if isinstance(value, list):
                setattr(task, key, ','.join(value))
            else:
                setattr(task, key, value)
        elif key != 'tags':
            setattr(task, key, value)

    task.updated_at = datetime.utcnow()
    db.session.commit()
    return task


def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return False
    db.session.delete(task)
    db.session.commit()
    return True


def search_tasks(query=None, status=None, priority=None, user_id=None):
    tasks = Task.query

    if query:
        tasks = tasks.filter(
            db.or_(
                Task.title.like(f'%{query}%'),
                Task.description.like(f'%{query}%')
            )
        )

    if status:
        tasks = tasks.filter(Task.status == status)

    if priority:
        tasks = tasks.filter(Task.priority == int(priority))

    if user_id:
        tasks = tasks.filter(Task.user_id == int(user_id))

    return [t.to_dict() for t in tasks.all()]


def get_task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    all_tasks = Task.query.all()
    overdue_count = sum(1 for t in all_tasks if _is_overdue(t))

    return {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue_count,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
    }
