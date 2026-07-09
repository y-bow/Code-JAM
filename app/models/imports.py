from ._ext import db, gen_uuid
from datetime import datetime


class ImportBatch(db.Model):
    __tablename__ = 'import_batches'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    school_id = db.Column(db.String(36), db.ForeignKey('schools.id'), nullable=False)
    import_type = db.Column(db.String(50), nullable=False)
    file_name = db.Column(db.String(255))
    total_rows = db.Column(db.Integer, default=0)
    success_count = db.Column(db.Integer, default=0)
    skipped_count = db.Column(db.Integer, default=0)
    updated_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    errors_json = db.Column(db.Text, nullable=True)
    conflict_strategy = db.Column(db.String(20), default='skip')
    status = db.Column(db.String(20), default='completed')
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reverted_at = db.Column(db.DateTime, nullable=True)

    school = db.relationship('School', foreign_keys=[school_id])
    creator = db.relationship('User', foreign_keys=[created_by])