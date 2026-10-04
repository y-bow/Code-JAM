from flask import Blueprint, render_template, request, redirect, url_for, g, flash
from ..middleware import institution_scoped, role_minimum
from ..models import db, CustomTask, TeacherTodo

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks',
                      template_folder='templates/tasks')


@tasks_bp.route('/', methods=['GET', 'POST'])
@institution_scoped
def tasks():
    user = g.current_user
    if request.method == 'POST':
        title = request.form.get('title')
        due_date_str = request.form.get('due_date')
        from datetime import datetime
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        new_task = CustomTask(user_id=user.id, title=title, due_date=due_date)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('tasks.tasks'))

    custom_tasks = (
        CustomTask.query
        .filter_by(user_id=user.id)
        .order_by(CustomTask.is_completed, CustomTask.due_date.asc())
        .all()
    )
    custom_tasks.sort(key=lambda x: (x.is_completed, x.due_date is None, x.due_date))
    return render_template('tasks.html', custom_tasks=custom_tasks)


@tasks_bp.route('/toggle/<string:task_id>', methods=['POST'])
@institution_scoped
def toggle_task(task_id):
    task = CustomTask.query.get_or_404(task_id)
    if task.user_id == g.current_user.id:
        task.is_completed = not task.is_completed
        db.session.commit()
    return redirect(url_for('tasks.tasks'))


@tasks_bp.route('/delete/<string:task_id>', methods=['POST'])
@institution_scoped
def delete_task(task_id):
    task = CustomTask.query.get_or_404(task_id)
    if task.user_id == g.current_user.id:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('tasks.tasks'))


@tasks_bp.route('/teacher/add', methods=['POST'])
@institution_scoped
@role_minimum('assistant_professor')
def add_teacher_task():
    title = request.form.get('title')
    if title:
        new_task = TeacherTodo(teacher_id=g.current_user.id, title=title)
        db.session.add(new_task)
        db.session.commit()
    return redirect(url_for('academics.teacher_dashboard'))


@tasks_bp.route('/teacher/toggle/<string:task_id>', methods=['POST'])
@institution_scoped
@role_minimum('assistant_professor')
def toggle_teacher_task(task_id):
    task = TeacherTodo.query.get_or_404(task_id)
    if task.teacher_id == g.current_user.id:
        task.is_completed = not task.is_completed
        db.session.commit()
    return redirect(url_for('academics.teacher_dashboard'))


@tasks_bp.route('/teacher/delete/<string:task_id>', methods=['POST'])
@institution_scoped
@role_minimum('assistant_professor')
def delete_teacher_task(task_id):
    task = TeacherTodo.query.get_or_404(task_id)
    if task.teacher_id == g.current_user.id:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('academics.teacher_dashboard'))
