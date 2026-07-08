from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..services.setup_service import (
    is_setup_complete, has_admin_users, has_any_schools,
    create_admin_account, create_institution, create_academic_year,
    create_department, create_section, save_theme_settings, mark_setup_complete,
)
from ..services import import_service
from ..models import db, School, Department

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
            school = School.query.first()
            if not school:
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

            year, err = create_academic_year(year_name, start_date, end_date, school.id)
            if err:
                return render_template('setup_wizard.html', step=step, steps=STEPS,
                                       step_labels=STEP_LABELS, errors=[err],
                                       form_data=request.form)

            dept_names = request.form.getlist('dept_name[]')
            dept_codes = request.form.getlist('dept_code[]')
            for dn, dc in zip(dept_names, dept_codes):
                if dn.strip() and dc.strip():
                    create_department(dn.strip(), dc.strip(), school.id)

            sec_names = request.form.getlist('sec_name[]')
            sec_codes = request.form.getlist('sec_code[]')
            sec_depts = request.form.getlist('sec_dept_code[]')
            sec_years = request.form.getlist('sec_batch_year[]')
            for sn, sc, sd, sy in zip(sec_names, sec_codes, sec_depts, sec_years):
                if sn.strip() and sc.strip() and sd.strip():
                    dept = Department.query.filter_by(school_id=school.id, code=sd.strip()).first()
                    if dept:
                        create_section(sn.strip(), sc.strip(), dept.id, sy or str(datetime.utcnow().year), school.id)

            return redirect(url_for('setup.wizard', step='import'))

        elif step == 'import':
            school = School.query.first()
            if not school:
                return redirect(url_for('setup.wizard', step='institution'))

            files = request.files.getlist('import_files')
            results = []
            all_successful = True

            for f in files:
                if not f or not f.filename:
                    continue
                parsed, err = import_service.parse_upload(f)
                if err:
                    results.append({'file': f.filename, 'status': 'error', 'message': err})
                    all_successful = False
                    continue
                import_type = import_service.detect_import_type(parsed['columns'])
                if not import_type:
                    results.append({'file': f.filename, 'status': 'warning', 'message': 'Could not detect import type from columns. Skipped.'})
                    continue
                validated, err = import_service.validate_import(parsed, import_type, school.id)
                if err:
                    results.append({'file': f.filename, 'status': 'error', 'message': err})
                    all_successful = False
                    continue
                invalid = [r for r in validated if not r['valid']]
                if invalid:
                    errors_list = [f'Row {r["index"]+1}: {"; ".join(r["errors"])}' for r in invalid]
                    results.append({'file': f.filename, 'status': 'error', 'message': f'{len(invalid)} row(s) invalid', 'details': errors_list})
                    all_successful = False
                    continue
                batch, err = import_service.execute_import(validated, import_type, school.id, session.get('user_id') or 0)
                if err:
                    results.append({'file': f.filename, 'status': 'error', 'message': err})
                    all_successful = False
                else:
                    results.append({'file': f.filename, 'status': 'success', 'message': f'Imported {batch.success_count} {import_type}'})

            return render_template('setup_wizard.html', step=step, steps=STEPS,
                                   step_labels=STEP_LABELS, errors=None,
                                   import_results=results,
                                   form_data=request.form)

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
    if step == 'academic' and not has_any_schools():
        return redirect(url_for('setup.wizard', step='institution'))
    if step == 'import' and not has_any_schools():
        return redirect(url_for('setup.wizard', step='institution'))
    if step == 'complete' and not has_any_schools():
        return redirect(url_for('setup.wizard', step='institution'))

    return render_template('setup_wizard.html', step=step, steps=STEPS,
                           step_labels=STEP_LABELS, errors=None,
                           import_results=None, form_data=initial_data)
