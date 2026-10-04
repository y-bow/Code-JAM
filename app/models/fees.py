from datetime import datetime
from ._ext import db, gen_uuid


class Fee(db.Model):
    __tablename__ = 'fees'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    tuition_fee = db.Column(db.Float, default=0.0)
    lab_fee = db.Column(db.Float, default=0.0)
    library_fee = db.Column(db.Float, default=0.0)
    exam_fee = db.Column(db.Float, default=0.0)
    other_charges = db.Column(db.Float, default=0.0)

    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('User', backref=db.backref('fee_profile', uselist=False))

    @property
    def total_amount(self):
        return (self.tuition_fee or 0) + (self.lab_fee or 0) + (self.library_fee or 0) + (self.exam_fee or 0) + (self.other_charges or 0)

    @property
    def amount_paid(self):
        return sum(p.amount for p in self.payments if p.status == 'success')

    @property
    def remaining_balance(self):
        return max(0, self.total_amount - self.amount_paid)

    @property
    def payment_status(self):
        paid = self.amount_paid
        total = self.total_amount
        if total == 0:
            return 'Paid'
        if paid >= total:
            return 'Paid'
        elif paid > 0:
            return 'Partially Paid'
        else:
            return 'Pending'


class FeePayment(db.Model):
    __tablename__ = 'fee_payments'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    fee_id = db.Column(db.String(36), db.ForeignKey('fees.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')
    transaction_id = db.Column(db.String(100), unique=True)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

    fee = db.relationship('Fee', backref=db.backref('payments', lazy='dynamic', cascade='all, delete-orphan'))
