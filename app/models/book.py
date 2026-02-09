from datetime import datetime
from app import db

class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    is_important = db.Column(db.Boolean, default=False)  # Important books cannot be reissued
    quantity = db.Column(db.Integer, default=1)
    quantity_available = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    borrows = db.relationship('BookBorrow', backref='book', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'isbn': self.isbn,
            'is_important': self.is_important,
            'quantity': self.quantity,
            'quantity_available': self.quantity_available
        }
    
    def __repr__(self):
        return f'<Book {self.title}>'


class BookBorrow(db.Model):
    __tablename__ = 'book_borrows'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime, nullable=True)
    renewal_count = db.Column(db.Integer, default=0)  # Max 2 renewals allowed
    fine_amount = db.Column(db.Float, default=0.0)  # ₹1 per day overdue
    fine_paid = db.Column(db.Boolean, default=False)
    
    # Relationships
    student = db.relationship('Student', backref=db.backref('book_borrows', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'book_id': self.book_id,
            'book_title': self.book.title if self.book else None,
            'book_author': self.book.author if self.book else None,
            'is_important': self.book.is_important if self.book else False,
            'borrow_date': self.borrow_date.isoformat() + 'Z' if self.borrow_date else None,
            'due_date': self.due_date.isoformat() + 'Z' if self.due_date else None,
            'return_date': self.return_date.isoformat() + 'Z' if self.return_date else None,
            'renewal_count': self.renewal_count,
            'fine_amount': self.fine_amount,
            'fine_paid': self.fine_paid
        }
    
    def __repr__(self):
        return f'<BookBorrow {self.book.title if self.book else "Unknown"} by {self.student.name if self.student else "Unknown"}>'
