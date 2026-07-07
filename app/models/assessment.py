from datetime import datetime
from ._ext import db, gen_uuid


class Assignment(db.Model):
    __tablename__ = 'assignments'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime, nullable=False)
    points = db.Column(db.Integer, nullable=False)

    submissions = db.relationship('Submission', backref='assignment', lazy='dynamic',
                                  cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('ix_assignment_course', 'course_id'),
    )


class Submission(db.Model):
    __tablename__ = 'submissions'

    assignment_id = db.Column(db.String(36), db.ForeignKey('assignments.id'), primary_key=True)
    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    file_url = db.Column(db.String(500))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    grade = db.Column(db.Float)
    feedback = db.Column(db.Text)

    student = db.relationship('User', backref=db.backref('submissions', lazy='dynamic'))

    __table_args__ = (
        db.Index('ix_submission_student', 'student_id'),
    )


class Quiz(db.Model):
    __tablename__ = 'quizzes'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    time_limit = db.Column(db.Integer)
    questions = db.Column(db.Text)

    attempts = db.relationship('QuizAttempt', backref='quiz', lazy='dynamic',
                               cascade='all, delete-orphan')


class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'

    quiz_id = db.Column(db.String(36), db.ForeignKey('quizzes.id'), primary_key=True)
    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    answers = db.Column(db.Text)
    score = db.Column(db.Float)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('User', backref=db.backref('quiz_attempts', lazy='dynamic'))


class Grade(db.Model):
    __tablename__ = 'grades'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    grade = db.Column(db.Float, nullable=False)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('User', backref=db.backref('grades', lazy='dynamic'))
    course = db.relationship('Course', backref=db.backref('grades', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='uq_grade_student_course'),
        db.Index('ix_grade_student', 'student_id'),
    )


class Streak(db.Model):
    __tablename__ = 'streaks'

    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    current_streak_days = db.Column(db.Integer, default=0)
    last_deadline_met_date = db.Column(db.Date)
    badges_earned = db.Column(db.Text)

    student = db.relationship('User', backref=db.backref('streak', uselist=False))
