from app import create_app, db
from app.models.book import Book

app = create_app()

def seed_books():
    with app.app_context():
        # First check if books already exist to avoid duplicates
        if Book.query.count() > 0:
            print("📚 Books already exist in database. Skipping seeding.")
            return

        print("🌱 Seeding example books...")
        books = [
            Book(
                title="Introduction to Algorithms",
                author="Thomas H. Cormen, et al.",
                isbn="9780262033848",
                total_copies=3,
                available_copies=3,
                is_important=True
            ),
            Book(
                title="The Pragmatic Programmer",
                author="Andrew Hunt & David Thomas",
                isbn="9780135957059",
                total_copies=5,
                available_copies=5,
                is_important=False
            ),
            Book(
                title="Clean Code",
                author="Robert C. Martin",
                isbn="9780132350884",
                total_copies=4,
                available_copies=4,
                is_important=False
            ),
            Book(
                title="Computer Networking: A Top-Down Approach",
                author="James Kurose & Keith Ross",
                isbn="9780133594140",
                total_copies=2,
                available_copies=2,
                is_important=True
            ),
            Book(
                title="Design Patterns",
                author="Erich Gamma, et al.",
                isbn="9780201633610",
                total_copies=6,
                available_copies=6,
                is_important=False
            )
        ]
        
        db.session.add_all(books)
        db.session.commit()
        print("✅ Seeding complete!")

if __name__ == "__main__":
    # Ensure tables are created first
    with app.app_context():
        db.create_all()
    seed_books()
