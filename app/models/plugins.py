from datetime import datetime
from ._ext import db, gen_uuid


class PluginState(db.Model):
    __tablename__ = 'plugin_states'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    version = db.Column(db.String(20), default='0.0.0')
    installed_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
