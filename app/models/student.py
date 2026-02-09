from datetime import datetime
from app import db

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    rfid_uid = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(50), unique=True, nullable=False)
    department = db.Column(db.String(100))
    email = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    is_inside = db.Column(db.Boolean, default=False)  # Track if currently in library
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendance_logs = db.relationship('AttendanceLog', backref='student', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'rfid_uid': self.rfid_uid,
            'name': self.name,
            'roll_number': self.roll_number,
            'department': self.department,
            'email': self.email,
            'is_active': self.is_active,
            'is_inside': self.is_inside,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Student {self.name} ({self.roll_number})>'
