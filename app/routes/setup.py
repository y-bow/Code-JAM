import json
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..services.setup_service import (
    is_setup_complete, has_admin_users, has_any_institutions,
    create_admin_account, create_institution, create_academic_year,
    save_theme_settings, mark_setup_complete,
)
from ..services import import_service
from ..models import db, Institution

logger = logging.getLogger(__name__)

setup_bp = Blueprint('setup', __name__, url_prefix='/setup',
                      template_folder='templates/setup')


@setup_bp.before_request
def check_not_configured():
    if is_setup_complete():
        return redirect(url_for('index'))


STEPS = ['admin', 'institution', 'theme', 'academic', 'import', 'complete']
STEP_LABELS = ['Admin Account', 'Institution', 'Theme', 'Academic Config', 'Data Import', 'Complete']


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
            return redirect(url_for('setup.wizard', step='academic'))

        elif step == 'academic':
            institution = Institution.query.first()
            if not institution:
                return redirect(url_for('setup.wizard', step='institution'))

            errors = []
            year_name = request.form.get('year_name', '').strip()
            start_date = request.form.get('start_date', '').strip()
            end_date = request.form.get('end_date', '').strip()

            if not year_name:
                errors.append('Academic year name is required')
            if not start_date:
                errors.append('Start date is required')
            if not end_date:
                errors.append('End date is required')

            if errors:
                return render_template('setup_wizard.html', step=step, steps=STEPS,
                                       step_labels=STEP_LABELS, errors=errors,
                                       form_data=request.form)

            year, err = create_academic_year(year_name, start_date, end_date, institution.id)
            if err:
                return render_template('setup_wizard.html', step=step, steps=STEPS,
                                       step_labels=STEP_LABELS, errors=[err],
                                       form_data=request.form)

            return redirect(url_for('setup.wizard', step='import'))

        elif step == 'import':
            institution = Institution.query.first()
            if not institution:
                return redirect(url_for('setup.wizard', step='institution'))

            conflict_strategy = request.form.get('conflict_strategy', 'skip')
            files = request.files.getlist('import_files')
            files_data = []
            results = []

            for f in files:
                if not f or not f.filename:
                    continue
                parsed, err = import_service.parse_upload(f)
                if err:
                    results.append({'file': f.filename, 'status': 'error', 'message': err})
                    continue

                import_type = import_service.detect_import_type_from_filename(f.filename)
                if not import_type:
                    import_type = import_service.detect_import_type(parsed['columns'])
                if not import_type:
                    results.append({
                        'file': f.filename, 'status': 'warning',
                        'message': 'Could not detect import type from filename or columns. Skipped.',
                    })
                    continue

                files_data.append({
                    'filename': f.filename,
                    'import_type': import_type,
                    'parsed': parsed,
                })

            if files_data:
                batch_results = import_service.batch_import(
                    files_data, institution.id, session.get('user_id') or 0, conflict_strategy,
                )
                results.extend(batch_results)

            all_successful = all(r['status'] == 'success' for r in results)

            return render_template('setup_wizard.html', step=step, steps=STEPS,
                                   step_labels=STEP_LABELS, errors=None,
                                   import_results=results,
                                   all_imports_successful=all_successful,
                                   form_data=request.form)

        elif step == 'complete':
            mark_setup_complete()
            session.clear()
            flash('Setup complete! Please log in with your admin credentials.', 'success')
            return redirect(url_for('auth.login'))

    initial_data = {}
    if step == 'institution' and not has_admin_users():
        return redirect(url_for('setup.wizard', step='admin'))
    if step == 'theme' and not has_any_institutions():
        return redirect(url_for('setup.wizard', step='institution'))
    if step == 'academic' and not has_any_institutions():
        return redirect(url_for('setup.wizard', step='institution'))
    if step == 'import' and not has_any_institutions():
        return redirect(url_for('setup.wizard', step='institution'))
    if step == 'complete' and not has_any_institutions():
        return redirect(url_for('setup.wizard', step='institution'))

    return render_template('setup_wizard.html', step=step, steps=STEPS,
                           step_labels=STEP_LABELS, errors=None,
                           import_results=None, all_imports_successful=False,
                           form_data=initial_data)
