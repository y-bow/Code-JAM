import click
from flask.cli import AppGroup

hive_cli = AppGroup('hive', help='Hive administration commands.')


@hive_cli.command('create-admin')
@click.option('--name', prompt='Full Name', help='Admin full name')
@click.option('--email', prompt='Email', help='Admin email address')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Admin password')
@click.option('--role', default='superadmin', show_default=True, type=click.Choice(['admin', 'superadmin']))
def create_admin(name, email, password, role):
    from .models import db, User
    from .models._ext import bcrypt

    existing = User.query.filter_by(email=email).first()
    if existing:
        click.echo(f'Error: A user with email {email} already exists.')
        return

    school_id = None
    if role == 'admin':
        from .models import School
        schools = School.query.all()
        if len(schools) == 1:
            school_id = schools[0].id
        elif len(schools) > 1:
            click.echo('Multiple schools exist. Use --school-id to specify.')
            return

    from .models.auth import generate_username
    cleaned_email = email.strip().lower()
    user = User(
        email=cleaned_email,
        username=generate_username(cleaned_email, school_id),
        password_hash=bcrypt.generate_password_hash(password).decode('utf-8'),
        role=role,
        name=name.strip(),
        school_id=school_id,
    )
    db.session.add(user)
    db.session.commit()
    click.echo(f'Created {role} user: {name} <{email}>')


@hive_cli.command('backup')
@click.option('--output', '-o', default='hive_backup.sql', help='Output file path')
def backup_db(output):
    import subprocess
    import os
    from flask import current_app

    db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    if db_uri.startswith('sqlite'):
        db_path = db_uri.replace('sqlite:///', '')
        if not os.path.exists(db_path):
            click.echo(f'Error: Database not found at {db_path}')
            return
        import shutil
        shutil.copy2(db_path, output)
        click.echo(f'SQLite database backed up to {output}')
    elif db_uri.startswith('postgresql'):
        import re
        match = re.match(r'postgresql://(.+):(.+)@(.+)/(.+)', db_uri)
        if match:
            user, pw, host, dbname = match.groups()
            os.environ['PGPASSWORD'] = pw
            result = subprocess.run(
                ['pg_dump', '-h', host, '-U', user, '-d', dbname, '-f', output],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                click.echo(f'PostgreSQL database backed up to {output}')
            else:
                click.echo(f'Backup failed: {result.stderr}')
        else:
            click.echo('Could not parse PostgreSQL URI.')
    else:
        click.echo(f'Unsupported database type for backup.')


@hive_cli.command('import')
@click.argument('import_type', type=click.Choice([
    'students', 'faculty', 'courses', 'timetable', 'enrollments',
    'departments', 'sections', 'clubs', 'attendance', 'grades',
]))
@click.option('--file', '-f', required=True, type=click.Path(exists=True), help='CSV/XLSX file path')
@click.option('--school-id', required=True, help='School ID for scoping the import')
@click.option('--dry-run', is_flag=True, help='Validate without inserting')
@click.option('--user-id', help='User ID for audit tracking')
def import_data(import_type, file, school_id, dry_run, user_id):
    from .services.import_service import parse_upload, validate_import, execute_import
    from werkzeug.datastructures import FileStorage

    with open(file, 'rb') as f:
        fs = FileStorage(stream=f, filename=file)
        parsed, error = parse_upload(fs)

    if error:
        click.echo(f'Error parsing file: {error}')
        return

    validated, error = validate_import(parsed, import_type, school_id)
    if error:
        click.echo(f'Validation error: {error}')
        return

    valid_count = sum(1 for v in validated if v['valid'])
    error_count = sum(1 for v in validated if not v['valid'])

    click.echo(f'Total rows: {len(validated)}')
    click.echo(f'Valid: {valid_count}')
    click.echo(f'Errors: {error_count}')

    if error_count > 0:
        click.echo('\nValidation errors:')
        for v in validated:
            if not v['valid']:
                click.echo(f'  Row {v["index"] + 1}: {", ".join(v["errors"])}')

    if dry_run:
        click.echo('\nDry run complete. No data inserted.')
        return

    if valid_count == 0:
        click.echo('No valid rows to import.')
        return

    click.confirm(f'\nImport {valid_count} rows?', abort=True)

    uid = user_id or 'cli'
    batch, error = execute_import(validated, import_type, school_id, uid)
    if error:
        click.echo(f'Import failed: {error}')
        return

    click.echo(f'\nImport completed:')
    click.echo(f'  Batch ID: {batch.id}')
    click.echo(f'  Success: {batch.success_count}')
    click.echo(f'  Errors: {batch.error_count}')
