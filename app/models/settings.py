from ._ext import db


class SiteSetting(db.Model):
    __tablename__ = 'site_settings'

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(20), default='string')
    category = db.Column(db.String(50), default='general')
    description = db.Column(db.String(200))

    def get_typed_value(self):
        if self.value is None:
            return None
        if self.value_type == 'int':
            return int(self.value)
        if self.value_type == 'float':
            return float(self.value)
        if self.value_type == 'bool':
            return self.value.lower() in ('true', '1', 'yes')
        return self.value


def get_setting(key, default=None):
    setting = SiteSetting.query.get(key)
    if setting is None:
        return default
    return setting.get_typed_value()


def set_setting(key, value, value_type='string', category='general', description=''):
    setting = SiteSetting.query.get(key)
    if setting is None:
        setting = SiteSetting(key=key, value_type=value_type, category=category, description=description)
        db.session.add(setting)
    setting.value = str(value) if value is not None else None
    db.session.commit()
