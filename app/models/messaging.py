from datetime import datetime
from ._ext import db, gen_uuid


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    is_deleted_by_sender = db.Column(db.Boolean, default=False)
    is_deleted_by_recipient = db.Column(db.Boolean, default=False)
    thread_id = db.Column(db.String(36), db.ForeignKey('messages.id'), nullable=True)

    sender = db.relationship('User', foreign_keys=[sender_id],
                             backref=db.backref('sent_messages', lazy='dynamic'))
    recipient = db.relationship('User', foreign_keys=[recipient_id],
                                backref=db.backref('received_messages', lazy='dynamic'))
    replies = db.relationship('Message', backref=db.backref('parent', remote_side=[id]))


class MessageLog(db.Model):
    __tablename__ = 'message_logs'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    recipient_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    subject = db.Column(db.String(100))
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    was_blocked = db.Column(db.Boolean, default=False)
    block_reason = db.Column(db.String(200))


class Announcement(db.Model):
    __tablename__ = 'announcements'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    school_id = db.Column(db.String(36), db.ForeignKey('schools.id'), nullable=False)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=True)
    section_id = db.Column(db.String(36), db.ForeignKey('sections.id'), nullable=True)
    teacher_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    urgent = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(50), default='general')
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship('Course', backref=db.backref('announcements', lazy='dynamic'))
    section = db.relationship('Section', backref=db.backref('announcements', lazy='dynamic'))
    author = db.relationship('User', backref=db.backref('authored_announcements', lazy='dynamic'))

    __table_args__ = (
        db.Index('ix_announcement_school', 'school_id'),
        db.Index('ix_announcement_course', 'course_id'),
        db.Index('ix_announcement_section', 'section_id'),
    )


class Resource(db.Model):
    __tablename__ = 'resources'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    file_name = db.Column(db.String(200), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(50))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
