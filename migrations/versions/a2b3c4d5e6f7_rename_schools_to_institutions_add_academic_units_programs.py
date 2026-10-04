"""rename schools to institutions, add academic_units and programs

Revision ID: a2b3c4d5e6f7
Revises: 113abf13ffef
Create Date: 2026-07-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import uuid

revision = 'a2b3c4d5e6f7'
down_revision = '27935e2c156e'
branch_labels = None
depends_on = None


def gen_uuid():
    return str(uuid.uuid4())


def upgrade():
    conn = op.get_bind()

    # ── 1. Rename schools → institutions ──
    op.rename_table('schools', 'institutions')

    # Add new columns to institutions (created_at already exists from schools)
    op.add_column('institutions', sa.Column('has_academic_units', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('institutions', sa.Column('academic_unit_label', sa.String(length=50), nullable=False, server_default='School'))

    # ── 2. Create academic_units table ──
    op.create_table('academic_units',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('institution_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('institution_id', 'code', name='uq_academic_unit_institution_code')
    )
    op.create_index('ix_academic_unit_institution', 'academic_units', ['institution_id'])

    # ── 3. Create programs table ──
    op.create_table('programs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('department_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('duration_years', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('department_id', 'code', name='uq_program_department_code')
    )
    op.create_index('ix_program_department', 'programs', ['department_id'])

    # ── 4. Migrate departments: add institution_id, drop school_id ──
    with op.batch_alter_table('departments') as batch_op:
        batch_op.add_column(sa.Column('institution_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('academic_unit_id', sa.String(length=36), nullable=True))

    conn.execute(sa.text(
        "UPDATE departments SET institution_id = school_id WHERE school_id IS NOT NULL"
    ))

    with op.batch_alter_table('departments') as batch_op:
        batch_op.alter_column('institution_id', nullable=False)
        batch_op.create_index('ix_department_institution', ['institution_id'])
        batch_op.create_index('ix_department_academic_unit', ['academic_unit_id'])
        batch_op.create_foreign_key('fk_departments_institution', 'institutions',
                                    ['institution_id'], ['id'])
        batch_op.create_foreign_key('fk_departments_academic_unit', 'academic_units',
                                    ['academic_unit_id'], ['id'])
        batch_op.drop_index('ix_department_school')
        batch_op.drop_column('school_id')

    # ── 5. Migrate sections: add institution_id, program_id, drop school_id ──
    with op.batch_alter_table('sections') as batch_op:
        batch_op.add_column(sa.Column('institution_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('program_id', sa.String(length=36), nullable=True))

    conn.execute(sa.text(
        "UPDATE sections SET institution_id = school_id WHERE school_id IS NOT NULL"
    ))

    # Create programs from existing departments + batch_year combos
    dept_years = conn.execute(sa.text(
        "SELECT DISTINCT department_id, batch_year FROM sections WHERE department_id IS NOT NULL"
    )).fetchall()

    for dept_id, batch_year in dept_years:
        prog_id = gen_uuid()
        program_code = f"P{batch_year}-{dept_id[:8]}"
        conn.execute(sa.text(
            "INSERT INTO programs (id, department_id, name, code, duration_years, created_at) "
            "VALUES (:id, :dept_id, :name, :code, 4, datetime('now'))"
        ).bindparams(id=prog_id, dept_id=dept_id, name=f"Program {batch_year}", code=program_code))

        conn.execute(sa.text(
            "UPDATE sections SET program_id = :prog_id WHERE department_id = :dept_id AND batch_year = :year"
        ).bindparams(prog_id=prog_id, dept_id=dept_id, year=batch_year))

    # Fallback for sections without department
    null_progs = conn.execute(sa.text(
        "SELECT id, name, batch_year FROM sections WHERE program_id IS NULL"
    )).fetchall()
    for sec_id, sec_name, batch_year in null_progs:
        prog_id = gen_uuid()
        prog_code = f"GEN-{batch_year}-{sec_id[:8]}"
        conn.execute(sa.text(
            "INSERT INTO programs (id, department_id, name, code, duration_years, created_at) "
            "VALUES (:id, NULL, :name, :code, 4, datetime('now'))"
        ).bindparams(id=prog_id, name=f"General Program {batch_year}", code=prog_code))
        conn.execute(sa.text(
            "UPDATE sections SET program_id = :prog_id WHERE id = :sec_id"
        ).bindparams(prog_id=prog_id, sec_id=sec_id))

    with op.batch_alter_table('sections') as batch_op:
        batch_op.alter_column('institution_id', nullable=False)
        batch_op.alter_column('program_id', nullable=False)
        batch_op.create_index('ix_section_institution', ['institution_id'])
        batch_op.create_index('ix_section_program', ['program_id'])
        batch_op.create_foreign_key('fk_sections_institution', 'institutions',
                                    ['institution_id'], ['id'])
        batch_op.create_foreign_key('fk_sections_program', 'programs',
                                    ['program_id'], ['id'])
        batch_op.drop_column('school_id')
        batch_op.drop_index('ix_section_school')

    # ── 6. Migrate users: rename school_id → institution_id, update indexes ──
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_index('ix_user_role')
        batch_op.drop_index('ix_user_school')
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('school_id', new_column_name='institution_id')
    with op.batch_alter_table('users') as batch_op:
        batch_op.create_index('ix_user_institution', ['institution_id'])
        batch_op.create_index('ix_user_role', ['institution_id', 'role'])

    # ── 7. Migrate announcements ──
    with op.batch_alter_table('announcements') as batch_op:
        batch_op.drop_index('ix_announcement_school')
    with op.batch_alter_table('announcements') as batch_op:
        batch_op.alter_column('school_id', new_column_name='institution_id')
    with op.batch_alter_table('announcements') as batch_op:
        batch_op.create_index('ix_announcement_institution', ['institution_id'])

    # ── 8. Migrate lost_found_items ──
    with op.batch_alter_table('lost_found_items') as batch_op:
        batch_op.alter_column('school_id', new_column_name='institution_id')

    # ── 9. Migrate clubs ──
    with op.batch_alter_table('clubs') as batch_op:
        batch_op.drop_index('ix_club_school')
        batch_op.alter_column('school_id', new_column_name='institution_id')
    with op.batch_alter_table('clubs') as batch_op:
        batch_op.create_index('ix_club_institution', ['institution_id'])

    # ── 10. Migrate external_events ──
    with op.batch_alter_table('external_events') as batch_op:
        batch_op.drop_index('ix_event_school')
        batch_op.alter_column('school_id', new_column_name='institution_id')
    with op.batch_alter_table('external_events') as batch_op:
        batch_op.create_index('ix_event_institution', ['institution_id'])

    # ── 11. Migrate import_batches ──
    with op.batch_alter_table('import_batches') as batch_op:
        batch_op.alter_column('school_id', new_column_name='institution_id')

    # ── 12. Remove plugin_states table (cleanup) ──
    op.drop_table('plugin_states')

    # ── 13. Remove messaging tables (cleanup) ──
    op.drop_table('message_logs')
    op.drop_table('messages')




def downgrade():
    conn = op.get_bind()

    # ── Reverse users ──
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_index('ix_user_role')
        batch_op.drop_index('ix_user_institution')
        batch_op.alter_column('institution_id', new_column_name='school_id')
        batch_op.create_index('ix_user_school', ['school_id'])
        batch_op.create_index('ix_user_role', ['school_id', 'role'])

    # ── Reverse announcements ──
    with op.batch_alter_table('announcements') as batch_op:
        batch_op.drop_index('ix_announcement_institution')
        batch_op.alter_column('institution_id', new_column_name='school_id')
        batch_op.create_index('ix_announcement_school', ['school_id'])

    # ── Reverse lost_found_items ──
    with op.batch_alter_table('lost_found_items') as batch_op:
        batch_op.alter_column('institution_id', new_column_name='school_id')

    # ── Reverse clubs ──
    with op.batch_alter_table('clubs') as batch_op:
        batch_op.drop_index('ix_club_institution')
        batch_op.alter_column('institution_id', new_column_name='school_id')
        batch_op.create_index('ix_club_school', ['school_id'])

    # ── Reverse external_events ──
    with op.batch_alter_table('external_events') as batch_op:
        batch_op.drop_index('ix_event_institution')
        batch_op.alter_column('institution_id', new_column_name='school_id')
        batch_op.create_index('ix_event_school', ['school_id'])

    # ── Reverse import_batches ──
    with op.batch_alter_table('import_batches') as batch_op:
        batch_op.alter_column('institution_id', new_column_name='school_id')

    # ── Reverse sections ──
    with op.batch_alter_table('sections') as batch_op:
        batch_op.add_column(sa.Column('school_id', sa.String(length=36), nullable=True))
    conn.execute(sa.text("UPDATE sections SET school_id = institution_id"))
    with op.batch_alter_table('sections') as batch_op:
        batch_op.alter_column('school_id', nullable=False)
        batch_op.drop_index('ix_section_program')
        batch_op.drop_index('ix_section_institution')
        batch_op.drop_column('program_id')
        batch_op.drop_column('institution_id')
        batch_op.create_index('ix_section_school', ['school_id'])

    # ── Reverse departments ──
    with op.batch_alter_table('departments') as batch_op:
        batch_op.drop_index('ix_department_academic_unit')
        batch_op.drop_index('ix_department_institution')
        batch_op.drop_column('created_at')
        batch_op.drop_column('academic_unit_id')
        batch_op.drop_column('institution_id')
        batch_op.add_column(sa.Column('school_id', sa.String(length=36), nullable=True))
    conn.execute(sa.text("UPDATE departments SET school_id = institution_id"))
    with op.batch_alter_table('departments') as batch_op:
        batch_op.alter_column('school_id', nullable=False)

    # ── Drop tables ──
    op.drop_table('programs')
    op.drop_table('academic_units')

    # ── Drop new columns from institutions ──
    with op.batch_alter_table('institutions') as batch_op:
        batch_op.drop_column('created_at')
        batch_op.drop_column('academic_unit_label')
        batch_op.drop_column('has_academic_units')

    # ── Rename institutions → schools ──
    op.rename_table('institutions', 'schools')

    # ── Restore old tables ──
    # (messages, message_logs, plugin_states were dropped - downgrade can't restore data)
