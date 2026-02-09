from datetime import datetime
from app import db

class Apparatus(db.Model):
    __tablename__ = 'apparatus'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    quantity_available = db.Column(db.Integer, default=1)
    damage_fine = db.Column(db.Float, default=0.0)  # One-time damage fine amount
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    borrows = db.relationship('ApparatusBorrow', backref='apparatus', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'quantity': self.quantity,
            'quantity_available': self.quantity_available,
            'damage_fine': self.damage_fine
        }
    
    def __repr__(self):
        return f'<Apparatus {self.name}>'


class ApparatusBorrow(db.Model):
    __tablename__ = 'apparatus_borrows'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    apparatus_id = db.Column(db.Integer, db.ForeignKey('apparatus.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime, nullable=True)
    is_damaged = db.Column(db.Boolean, default=False)
    damage_fine = db.Column(db.Float, default=0.0)
    fine_paid = db.Column(db.Boolean, default=False)
    
    # Relationships
    student = db.relationship('Student', backref=db.backref('apparatus_borrows', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'apparatus_id': self.apparatus_id,
            'apparatus_name': self.apparatus.name if self.apparatus else None,
            'apparatus_category': self.apparatus.category if self.apparatus else None,
            'borrow_date': self.borrow_date.isoformat() + 'Z' if self.borrow_date else None,
            'return_date': self.return_date.isoformat() + 'Z' if self.return_date else None,
            'is_damaged': self.is_damaged,
            'damage_fine': self.damage_fine,
            'fine_paid': self.fine_paid
        }
    
    def __repr__(self):
        return f'<ApparatusBorrow {self.apparatus.name if self.apparatus else "Unknown"} by {self.student.name if self.student else "Unknown"}>'
