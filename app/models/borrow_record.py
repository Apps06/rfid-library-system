from datetime import datetime, timedelta
from app import db

class BorrowRecord(db.Model):
    __tablename__ = 'borrow_records'
    
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    borrowed_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, default=lambda: (datetime.utcnow() + timedelta(days=14)).replace(hour=23, minute=59, second=59, microsecond=0))
    returned_at = db.Column(db.DateTime, nullable=True)
    extensions_used = db.Column(db.Integer, default=0)
    fine_amount = db.Column(db.Float, default=0.0)
    fine_paid = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, RETURNED, OVERDUE
    
    def calculate_fine(self):
        """Calculate fine: ₹1 per day past due date"""
        if self.status == 'RETURNED' or self.fine_paid:
            return self.fine_amount
            
        now = datetime.utcnow()
        if now > self.due_date:
            # Calculate days overdue (difference in full days)
            delta = now - self.due_date
            # 1 second past midnight counts as 1 day overdue
            days_overdue = delta.days + (1 if delta.seconds > 0 or delta.microseconds > 0 else 0)
            self.fine_amount = float(max(0, days_overdue))
            self.status = 'OVERDUE'
        else:
            # If it was overdue but now (due to extension) it isn't, 
            # we keep any accrued fine but allow status to return to ACTIVE
            if self.status == 'OVERDUE':
                self.status = 'ACTIVE'
        return self.fine_amount

    def to_dict(self):
        # Update fine before returning dict
        self.calculate_fine()
        
        return {
            'id': self.id,
            'book_id': self.book_id,
            'book_title': self.book.title if self.book else None,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'borrowed_at': self.borrowed_at.isoformat() + 'Z' if self.borrowed_at else None,
            'due_date': self.due_date.isoformat() + 'Z' if self.due_date else None,
            'returned_at': self.returned_at.isoformat() + 'Z' if self.returned_at else None,
            'extensions_used': self.extensions_used,
            'fine_amount': self.fine_amount,
            'fine_paid': self.fine_paid,
            'status': self.status
        }
    
    def __repr__(self):
        return f'<BorrowRecord for Book {self.book_id}>'
