from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..services.setup_service import (
    is_setup_complete, has_admin_users, has_any_schools,
    create_admin_account, create_institution, save_theme_settings, mark_setup_complete,
)

setup_bp = Blueprint('setup', __name__, url_prefix='/setup',
                      template_folder='templates/setup')


@setup_bp.before_request
def check_not_configured():
    if is_setup_complete():
        return redirect(url_for('index'))


STEPS = ['admin', 'institution', 'theme', 'complete']
STEP_LABELS = ['Admin Account', 'Institution', 'Theme', 'Complete']


@setup_bp.route('/', methods=['GET', 'POST'])
def wizard():
    step = request.args.get('step', 'admin')
    if step not in STEPS:
        step = 'admin'

    if request.method == 'POST':
        action = request.form.get('action', 'next')

        if step == 'admin':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm = request.form.get('confirm_password', '')

            errors = []
            if not name:
                errors.append('Name is required')
            if not email or '@' not in email:
                errors.append('Valid email is required')
            if len(password) < 6:
                errors.append('Password must be at least 6 characters')
            if password != confirm:
                errors.append('Passwords do not match')

            if errors:
                return render_template('setup_wizard.html', step=step, steps=STEPS,
                                       step_labels=STEP_LABELS, errors=errors,
                                       form_data=request.form)

            user, error = create_admin_account(name, email, password)
            if error:
                return render_template('setup_wizard.html', step=step, steps=STEPS,
                                       step_labels=STEP_LABELS, errors=[error],
                                       form_data=request.form)

            session['user_id'] = user.id
            session['role'] = user.role
            session['name'] = user.name
            return redirect(url_for('setup.wizard', step='institution'))

        elif step == 'institution':
            name = request.form.get('name', '').strip()
            code = request.form.get('code', '').strip()

            errors = []
            if not name:
                errors.append('Institution name is required')
            if not code:
                errors.append('Institution code is required')

            if errors:
                return render_template('setup_wizard.html', step=step, steps=STEPS,
                                       step_labels=STEP_LABELS, errors=errors,
                                       form_data=request.form)

            create_institution(name, code)
            return redirect(url_for('setup.wizard', step='theme'))

        elif step == 'theme':
            primary_color = request.form.get('primary_color', '#6C63FF')
            theme_mode = request.form.get('theme_mode', 'light')
            save_theme_settings(primary_color, theme_mode)
            return redirect(url_for('setup.wizard', step='complete'))

        elif step == 'complete':
            mark_setup_complete()
            session.clear()
            flash('Setup complete! Please log in with your admin credentials.', 'success')
            return redirect(url_for('auth.login'))

    initial_data = {}
    if step == 'institution' and not has_admin_users():
        return redirect(url_for('setup.wizard', step='admin'))
    if step == 'theme' and not has_any_schools():
        return redirect(url_for('setup.wizard', step='institution'))

    return render_template('setup_wizard.html', step=step, steps=STEPS,
                           step_labels=STEP_LABELS, errors=None,
                           form_data=initial_data)
