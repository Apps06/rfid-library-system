from datetime import datetime
from app import db

class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    isbn = db.Column(db.String(20), unique=True)
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    is_important = db.Column(db.Boolean, default=False)  # Cannot be extended
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    borrows = db.relationship('BorrowRecord', backref='book', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'isbn': self.isbn,
            'total_copies': self.total_copies,
            'available_copies': self.available_copies,
            'is_important': self.is_important,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Book {self.title}>'
