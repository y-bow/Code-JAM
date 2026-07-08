import json
from flask import Blueprint, render_template, request, redirect, url_for, g, flash
from ..middleware import school_scoped, role_minimum
from ..services.import_service import (
    parse_upload, detect_import_type, validate_import, execute_import,
    get_recent_batches, IMPORT_TYPES, COLUMN_MAPS,
)

import_bp = Blueprint('imports', __name__, url_prefix='/imports',
                       template_folder='templates/imports')


@import_bp.route('/', methods=['GET'])
@school_scoped
@role_minimum('admin')
def index():
    batches = get_recent_batches(g.school_id)
    return render_template('import_upload.html',
                           import_types=IMPORT_TYPES,
                           batches=batches)


@import_bp.route('/preview', methods=['POST'])
@school_scoped
@role_minimum('admin')
def preview():
    import_type = request.form.get('import_type', '')
    if import_type not in IMPORT_TYPES:
        flash('Invalid import type selected.', 'danger')
        return redirect(url_for('imports.index'))

    if 'file' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('imports.index'))

    file = request.files['file']
    if not file or file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('imports.index'))

    parsed, error = parse_upload(file)
    if error:
        flash(error, 'danger')
        return redirect(url_for('imports.index'))

    detected_type = detect_import_type(parsed['columns'])
    if not detected_type or detected_type != import_type:
        pass

    validated, error = validate_import(parsed, import_type, g.school_id)
    if error:
        flash(error, 'danger')
        return redirect(url_for('imports.index'))

    valid_count = sum(1 for v in validated if v['valid'])
    error_count = sum(1 for v in validated if not v['valid'])
    sample_rows = parsed['rows'][:5]
    columns = parsed['columns']

    file.seek(0)
    import io
    file_content = file.read().decode('utf-8-sig')

    return render_template('import_preview.html',
                           import_type=import_type,
                           columns=columns,
                           sample_rows=sample_rows,
                           total_rows=parsed['total'],
                           valid_count=valid_count,
                           error_count=error_count,
                           validated=validated,
                           file_content=file_content,
                           column_spec=COLUMN_MAPS.get(import_type, {}))


@import_bp.route('/confirm', methods=['POST'])
@school_scoped
@role_minimum('admin')
def confirm():
    import_type = request.form.get('import_type', '')
    validated_json = request.form.get('validated_data', '')
    file_content = request.form.get('file_content', '')

    if not validated_json:
        flash('No data to import.', 'danger')
        return redirect(url_for('imports.index'))

    validated = json.loads(validated_json)

    batch, error = execute_import(
        validated, import_type, g.school_id, g.current_user.id
    )
    if error:
        flash(error, 'danger')
        return redirect(url_for('imports.index'))

    flash(
        f'Import completed: {batch.success_count} rows inserted, '
        f'{batch.error_count} errors.',
        'success' if batch.error_count == 0 else 'warning',
    )
    return redirect(url_for('imports.index'))
