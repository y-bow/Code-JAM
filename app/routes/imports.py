import json
import logging
from flask import Blueprint, render_template, request, redirect, url_for, g, flash
from ..middleware import institution_scoped, role_minimum
from ..services.import_service import (
    parse_upload, detect_import_type, validate_import, execute_import,
    get_recent_batches, IMPORT_TYPES, COLUMN_MAPS,
)

logger = logging.getLogger(__name__)

import_bp = Blueprint('imports', __name__, url_prefix='/imports',
                       template_folder='templates/imports')


@import_bp.route('/', methods=['GET'])
@institution_scoped
@role_minimum('admin')
def index():
    batches = get_recent_batches(g.institution_id)
    return render_template('import_upload.html',
                           import_types=IMPORT_TYPES,
                           batches=batches)


@import_bp.route('/preview', methods=['POST'])
@institution_scoped
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
    if detected_type and detected_type != import_type:
        logger.warning(
            'Type mismatch: user selected=%s auto-detected=%s file=%s columns=%s',
            import_type, detected_type, file.filename, parsed['columns'],
        )

    conflict_strategy = request.form.get('conflict_strategy', 'skip')
    validated, error = validate_import(parsed, import_type, g.institution_id, conflict_strategy)
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
                           column_spec=COLUMN_MAPS.get(import_type, {}),
                           conflict_strategy=conflict_strategy)


@import_bp.route('/confirm', methods=['POST'])
@institution_scoped
@role_minimum('admin')
def confirm():
    import_type = request.form.get('import_type', '')
    validated_json = request.form.get('validated_data', '')
    conflict_strategy = request.form.get('conflict_strategy', 'skip')

    if not validated_json:
        flash('No data to import.', 'danger')
        return redirect(url_for('imports.index'))

    validated = json.loads(validated_json)

    logger.info(
        'confirm: import_type=%s valid_rows=%d invalid_rows=%d strategy=%s',
        import_type,
        sum(1 for v in validated if v['valid']),
        sum(1 for v in validated if not v['valid']),
        conflict_strategy,
    )

    batch, error = execute_import(
        validated, import_type, g.institution_id, g.current_user.id, conflict_strategy,
    )
    if error:
        flash(error, 'danger')
        return redirect(url_for('imports.index'))

    parts = []
    if batch.success_count:
        parts.append(f'{batch.success_count} inserted')
    if batch.skipped_count:
        parts.append(f'{batch.skipped_count} skipped')
    if batch.updated_count:
        parts.append(f'{batch.updated_count} updated')
    flash(
        f'Import completed: {", ".join(parts)}.',
        'success',
    )
    return redirect(url_for('imports.index'))
