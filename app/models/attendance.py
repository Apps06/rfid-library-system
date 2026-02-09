from datetime import datetime
from app import db

class AttendanceLog(db.Model):
    __tablename__ = 'attendance_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    rfid_uid = db.Column(db.String(50), nullable=False, index=True)
    action = db.Column(db.String(10), nullable=False)  # 'ENTRY' or 'EXIT'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    device_id = db.Column(db.String(50), default='GATE_01')  # Identify which reader
    zone = db.Column(db.String(50), default='Library')  # Library, Lab, Classroom
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'roll_number': self.student.roll_number if self.student else None,
            'rfid_uid': self.rfid_uid,
            'action': self.action,
            'timestamp': self.timestamp.isoformat() + 'Z' if self.timestamp else None,
            'device_id': self.device_id,
            'zone': self.zone
        }
    
    def __repr__(self):
        return f'<AttendanceLog {self.action} at {self.timestamp}>'
