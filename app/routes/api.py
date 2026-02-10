from datetime import datetime, timedelta
import json
import os
from flask import Blueprint, request, jsonify
from app import db
from app.models import Student, AttendanceLog, Admin, Book, BookBorrow, Apparatus, ApparatusBorrow

api_bp = Blueprint('api', __name__)

# Buffer to store the latest scan for each zone
# Format: { 'Library': 'UID123', 'Lab': 'UID456' }
scan_buffer = {}

@api_bp.route('/scan/latest/<zone>', methods=['GET'])
def get_latest_scan(zone):
    """Retrieve and clear the latest scan for a specific zone"""
    uid = scan_buffer.get(zone)
    if uid:
        # Clear buffer after retrieval to avoid repeated fills
        scan_buffer[zone] = None
        return jsonify({'success': True, 'rfid_uid': uid})
    return jsonify({'success': True, 'rfid_uid': None})

# ============== RFID SCAN ENDPOINT ==============
@api_bp.route('/scan', methods=['POST'])
def scan_rfid():
    """
    Main endpoint for RFID scanner.
    Receives RFID UID and logs entry/exit.
    """
    data = request.get_json()
    
    if not data or 'rfid_uid' not in data:
        return jsonify({'success': False, 'error': 'RFID UID required'}), 400
    
    rfid_uid = data['rfid_uid'].upper().strip()
    device_id = data.get('device_id', 'GATE_01')
    zone = data.get('zone', 'Library')  # Library, Lab, or Classroom

    # Store in buffer for the web UI
    scan_buffer[zone] = rfid_uid
    
    # Find student by RFID
    student = Student.query.filter_by(rfid_uid=rfid_uid, is_active=True).first()
    
    is_new_registration = False
    if not student:
        # AUTO-REGISTRATION LOGIC
        print(f"✨ Auto-registering new card: {rfid_uid}")
        student = Student(
            rfid_uid=rfid_uid,
            name=f"New Student ({rfid_uid})",
            roll_number=f"TEMP-{rfid_uid}",
            department="Auto-Registered",
            is_inside=False # Will be set to True below
        )
        db.session.add(student)
        db.session.commit()
        is_new_registration = True
    
    # Toggle entry/exit based on current state
    if student.is_inside:
        action = 'EXIT'
        student.is_inside = False
    else:
        action = 'ENTRY'
        student.is_inside = True
    
    # Create attendance log with zone
    log = AttendanceLog(
        student_id=student.id,
        rfid_uid=rfid_uid,
        action=action,
        device_id=device_id,
        zone=zone
    )
    
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'action': action,
        'log_id': log.id,
        'student': {
            'id': student.id,
            'name': student.name,
            'roll_number': student.roll_number,
            'department': student.department,
            'rfid_uid': student.rfid_uid
        },
        'timestamp': log.timestamp.isoformat() + 'Z'
    })


# ============== STUDENT ENDPOINTS ==============
@api_bp.route('/students', methods=['GET'])
def get_students():
    """Get all students"""
    students = Student.query.order_by(Student.name).all()
    return jsonify({
        'success': True,
        'students': [s.to_dict() for s in students],
        'count': len(students)
    })


@api_bp.route('/students', methods=['POST'])
def create_student():
    """Create a new student"""
    data = request.get_json()
    
    required = ['name', 'rfid_uid', 'roll_number']
    for field in required:
        if field not in data:
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    # Check if RFID or roll number already exists
    existing = Student.query.filter_by(rfid_uid=data['rfid_uid'].upper()).first()
    if existing:
        # If it's an auto-registered placeholder, perform a "Takeover" (Update)
        if existing.department == 'Auto-Registered' or existing.name.startswith('New Student'):
            existing.name = data['name'].strip()
            existing.roll_number = data['roll_number'].strip()
            existing.department = data.get('department', '')
            existing.email = data.get('email', '')
            db.session.commit()
            return jsonify({
                'success': True, 
                'student': existing.to_dict(), 
                'message': 'Merged with auto-registered record'
            }), 200
        else:
            return jsonify({'success': False, 'error': 'RFID UID already registered'}), 409
            
    if Student.query.filter_by(roll_number=data['roll_number']).first():
        return jsonify({'success': False, 'error': 'Roll number already exists'}), 409
    
    student = Student(
        rfid_uid=data['rfid_uid'].upper().strip(),
        name=data['name'].strip(),
        roll_number=data['roll_number'].strip(),
        department=data.get('department', ''),
        email=data.get('email', '')
    )
    
    db.session.add(student)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'student': student.to_dict()
    }), 201


@api_bp.route('/students/<int:id>', methods=['GET'])
def get_student(id):
    """Get a single student"""
    student = Student.query.get_or_404(id)
    return jsonify({'success': True, 'student': student.to_dict()})


@api_bp.route('/students/<int:id>', methods=['PUT'])
def update_student(id):
    """Update a student"""
    student = Student.query.get_or_404(id)
    data = request.get_json()
    
    if 'name' in data:
        student.name = data['name'].strip()
    if 'department' in data:
        student.department = data['department']
    if 'email' in data:
        student.email = data['email']
    if 'is_active' in data:
        student.is_active = data['is_active']
    if 'rfid_uid' in data:
        # Check for duplicate
        existing = Student.query.filter_by(rfid_uid=data['rfid_uid'].upper()).first()
        if existing and existing.id != id:
            return jsonify({'success': False, 'error': 'RFID UID already in use'}), 409
        student.rfid_uid = data['rfid_uid'].upper().strip()

    if 'roll_number' in data:
        # Check for duplicate roll number
        existing_roll = Student.query.filter_by(roll_number=data['roll_number']).first()
        if existing_roll and existing_roll.id != id:
            return jsonify({'success': False, 'error': 'Roll number already in use'}), 409
        student.roll_number = data['roll_number'].strip()
    
    db.session.commit()
    return jsonify({'success': True, 'student': student.to_dict()})


@api_bp.route('/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    """Delete a student and all related records"""
    student = Student.query.get_or_404(id)
    
    # Delete related records to handle foreign key constraints
    AttendanceLog.query.filter_by(student_id=id).delete()
    BookBorrow.query.filter_by(student_id=id).delete()
    ApparatusBorrow.query.filter_by(student_id=id).delete()
    
    db.session.delete(student)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Student and related records deleted'})


# ============== ATTENDANCE ENDPOINTS ==============
@api_bp.route('/attendance', methods=['GET'])
def get_attendance():
    """Get attendance logs with optional filters"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    date = request.args.get('date')  # Format: YYYY-MM-DD
    
    query = AttendanceLog.query.order_by(AttendanceLog.timestamp.desc())
    
    if date:
        try:
            filter_date = datetime.strptime(date, '%Y-%m-%d')
            query = query.filter(
                AttendanceLog.timestamp >= filter_date,
                AttendanceLog.timestamp < filter_date + timedelta(days=1)
            )
        except ValueError:
            pass
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@api_bp.route('/attendance/today', methods=['GET'])
def get_today_attendance():
    """Get today's attendance logs, optionally filtered by zone"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    zone = request.args.get('zone')  # Optional zone filter
    
    query = AttendanceLog.query.filter(
        AttendanceLog.timestamp >= today,
        AttendanceLog.timestamp < tomorrow
    )
    
    if zone:
        query = query.filter(AttendanceLog.zone == zone)
    
    logs = query.order_by(AttendanceLog.timestamp.desc()).all()
    
    return jsonify({
        'success': True,
        'logs': [log.to_dict() for log in logs],
        'count': len(logs)
    })


@api_bp.route('/attendance/export', methods=['GET'])
def export_attendance_csv():
    """Export attendance logs as CSV"""
    from flask import Response
    import csv
    import io
    
    zone = request.args.get('zone')  # Optional zone filter
    date = request.args.get('date')  # Optional date filter (YYYY-MM-DD)
    
    query = AttendanceLog.query.order_by(AttendanceLog.timestamp.desc())
    
    if zone:
        query = query.filter(AttendanceLog.zone == zone)
    
    if date:
        try:
            filter_date = datetime.strptime(date, '%Y-%m-%d')
            query = query.filter(
                AttendanceLog.timestamp >= filter_date,
                AttendanceLog.timestamp < filter_date + timedelta(days=1)
            )
        except ValueError:
            pass
    else:
        # Default to today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        query = query.filter(
            AttendanceLog.timestamp >= today,
            AttendanceLog.timestamp < tomorrow
        )
    
    logs = query.all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Student Name', 'Roll Number', 'RFID UID', 'Action', 'Timestamp', 'Zone', 'Device ID'])
    
    for log in logs:
        writer.writerow([
            log.id,
            log.student.name if log.student else 'Unknown',
            log.student.roll_number if log.student else 'N/A',
            log.rfid_uid,
            log.action,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else '',
            log.zone,
            log.device_id
        ])
    
    output.seek(0)
    
    zone_name = zone if zone else 'all'
    date_str = date if date else datetime.utcnow().strftime('%Y-%m-%d')
    filename = f'attendance_{zone_name}_{date_str}.csv'
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


# ============== DASHBOARD ENDPOINTS ==============
@api_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get statistics for dashboard"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    # Count students currently inside
    inside_count = Student.query.filter_by(is_inside=True).count()
    
    # Total registered students
    total_students = Student.query.filter_by(is_active=True).count()
    
    # Today's entry count
    today_entries = AttendanceLog.query.filter(
        AttendanceLog.timestamp >= today,
        AttendanceLog.timestamp < tomorrow,
        AttendanceLog.action == 'ENTRY'
    ).count()
    
    # Today's exit count
    today_exits = AttendanceLog.query.filter(
        AttendanceLog.timestamp >= today,
        AttendanceLog.timestamp < tomorrow,
        AttendanceLog.action == 'EXIT'
    ).count()
    
    # Recent activity (last 10 scans)
    recent_logs = AttendanceLog.query.order_by(
        AttendanceLog.timestamp.desc()
    ).limit(10).all()
    
    # Hourly breakdown for today
    hourly_data = []
    for hour in range(24):
        start = today + timedelta(hours=hour)
        end = start + timedelta(hours=1)
        count = AttendanceLog.query.filter(
            AttendanceLog.timestamp >= start,
            AttendanceLog.timestamp < end,
            AttendanceLog.action == 'ENTRY'
        ).count()
        hourly_data.append({'hour': hour, 'entries': count})
    
    return jsonify({
        'success': True,
        'stats': {
            'inside_count': inside_count,
            'total_students': total_students,
            'today_entries': today_entries,
            'today_exits': today_exits
        },
        'recent_activity': [log.to_dict() for log in recent_logs],
        'hourly_data': hourly_data
    })


# ============== ADMIN ENDPOINTS ==============
@api_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    admin = Admin.query.filter_by(username=data['username']).first()
    
    if admin and admin.check_password(data['password']):
        return jsonify({
            'success': True,
            'admin': admin.to_dict()
        })
    
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401


@api_bp.route('/admin/create', methods=['POST'])
def create_admin():
    """Create admin user (for initial setup)"""
    # Check if any admin exists
    if Admin.query.count() > 0:
        return jsonify({'success': False, 'error': 'Admin already exists'}), 403
    
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    admin = Admin(username=data['username'])
    admin.set_password(data['password'])
    
    db.session.add(admin)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Admin created',
        'admin': admin.to_dict()
    }), 201


# ============== LIBRARY ENDPOINTS ==============
def init_library_books():
    """Initialize library books from JSON if not already in database"""
    if Book.query.count() == 0:
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'books_data.json')
        if os.path.exists(data_path):
            with open(data_path, 'r') as f:
                books_data = json.load(f)
                for book_data in books_data:
                    book = Book(
                        title=book_data['title'],
                        author=book_data['author'],
                        isbn=book_data['isbn'],
                        is_important=book_data.get('is_important', False),
                        quantity=book_data.get('quantity', 1),
                        quantity_available=book_data.get('quantity', 1)
                    )
                    db.session.add(book)
                db.session.commit()

@api_bp.route('/library/books', methods=['GET'])
def get_library_books():
    """Get all library books"""
    init_library_books()
    books = Book.query.order_by(Book.title).all()
    return jsonify({
        'success': True,
        'books': [b.to_dict() for b in books],
        'count': len(books)
    })

@api_bp.route('/library/stats', methods=['GET'])
def get_library_stats():
    """Get library statistics"""
    init_library_books()
    total_books = Book.query.count()
    available_books = db.session.query(db.func.sum(Book.quantity_available)).scalar() or 0
    borrowed_count = BookBorrow.query.filter_by(return_date=None).count()
    
    # Calculate pending fines
    pending_fines = 0
    overdue_borrows = BookBorrow.query.filter(
        BookBorrow.return_date == None,
        BookBorrow.fine_paid == False,
        BookBorrow.fine_amount > 0
    ).all()
    pending_fines = sum(b.fine_amount for b in overdue_borrows)
    
    # Recent activity
    recent = BookBorrow.query.order_by(BookBorrow.borrow_date.desc()).limit(10).all()
    
    return jsonify({
        'success': True,
        'stats': {
            'total_books': total_books,
            'available_books': int(available_books),
            'borrowed_count': borrowed_count,
            'pending_fines': pending_fines
        },
        'recent_activity': [b.to_dict() for b in recent]
    })

@api_bp.route('/library/borrow', methods=['POST'])
def borrow_book():
    """Borrow a book"""
    data = request.get_json()
    book_id = data.get('book_id')
    student_identifier = data.get('student_identifier')
    
    if not book_id or not student_identifier:
        return jsonify({'success': False, 'error': 'Book ID and student identifier required'}), 400
    
    # Find student
    student = Student.query.filter(
        (Student.roll_number == student_identifier) | (Student.rfid_uid == student_identifier.upper())
    ).first()
    
    if not student:
        return jsonify({'success': False, 'error': 'Student not found'}), 404
    
    # Find book
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404
    
    if book.quantity_available <= 0:
        return jsonify({'success': False, 'error': 'Book not available'}), 400
    
    # Create borrow record
    due_date = datetime.utcnow() + timedelta(days=14)  # 2 weeks borrow period
    borrow = BookBorrow(
        student_id=student.id,
        book_id=book.id,
        due_date=due_date
    )
    
    book.quantity_available -= 1
    db.session.add(borrow)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'borrow': borrow.to_dict()
    })

@api_bp.route('/library/return', methods=['POST'])
def return_book():
    """Return a book"""
    data = request.get_json()
    borrow_id = data.get('borrow_id')
    sim_date = data.get('sim_date')
    
    if not borrow_id:
        return jsonify({'success': False, 'error': 'Borrow ID required'}), 400
    
    borrow = BookBorrow.query.get(borrow_id)
    if not borrow:
        return jsonify({'success': False, 'error': 'Borrow record not found'}), 404
    
    if borrow.return_date:
        return jsonify({'success': False, 'error': 'Book already returned'}), 400
    
    # Calculate fine based on simulation date
    current_date = datetime.strptime(sim_date, '%Y-%m-%d') if sim_date else datetime.utcnow()
    fine_amount = 0
    
    if current_date > borrow.due_date:
        days_overdue = (current_date - borrow.due_date).days
        fine_amount = days_overdue  # ₹1 per day
    
    borrow.return_date = current_date
    borrow.fine_amount = fine_amount
    borrow.book.quantity_available += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'fine_amount': fine_amount
    })

@api_bp.route('/library/extend', methods=['POST'])
def extend_book():
    """Extend book borrow period"""
    data = request.get_json()
    borrow_id = data.get('borrow_id')
    
    if not borrow_id:
        return jsonify({'success': False, 'error': 'Borrow ID required'}), 400
    
    borrow = BookBorrow.query.get(borrow_id)
    if not borrow:
        return jsonify({'success': False, 'error': 'Borrow record not found'}), 404
    
    if borrow.return_date:
        return jsonify({'success': False, 'error': 'Book already returned'}), 400
    
    if borrow.book.is_important:
        return jsonify({'success': False, 'error': 'Important books cannot be extended'}), 400
    
    if borrow.renewal_count >= 2:
        return jsonify({'success': False, 'error': 'Maximum renewals reached (2). Please return and re-borrow manually.'}), 400
    
    # Extend by 7 days
    borrow.due_date = borrow.due_date + timedelta(days=7)
    borrow.renewal_count += 1
    db.session.commit()
    
    return jsonify({
        'success': True,
        'borrow': borrow.to_dict()
    })

@api_bp.route('/library/borrowed', methods=['GET'])
def get_borrowed_books():
    """Get borrowed books for a student"""
    student_identifier = request.args.get('student_identifier')
    sim_date = request.args.get('sim_date')
    
    if not student_identifier:
        return jsonify({'success': False, 'error': 'Student identifier required'}), 400
    
    student = Student.query.filter(
        (Student.roll_number == student_identifier) | (Student.rfid_uid == student_identifier.upper())
    ).first()
    
    if not student:
        return jsonify({'success': False, 'error': 'Student not found'}), 404
    
    borrows = BookBorrow.query.filter_by(student_id=student.id).order_by(BookBorrow.borrow_date.desc()).all()
    
    # Update fine amounts based on simulation date
    current_date = datetime.strptime(sim_date, '%Y-%m-%d') if sim_date else datetime.utcnow()
    
    for b in borrows:
        if not b.return_date and current_date > b.due_date:
            days_overdue = (current_date - b.due_date).days
            b.fine_amount = days_overdue
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'borrows': [b.to_dict() for b in borrows]
    })

@api_bp.route('/library/fines', methods=['GET'])
def get_library_fines():
    """Get outstanding fines for a student"""
    student_identifier = request.args.get('student_identifier')
    sim_date = request.args.get('sim_date')
    
    if not student_identifier:
        return jsonify({'success': False, 'error': 'Student identifier required'}), 400
    
    student = Student.query.filter(
        (Student.roll_number == student_identifier) | (Student.rfid_uid == student_identifier.upper())
    ).first()
    
    if not student:
        return jsonify({'success': False, 'error': 'Student not found'}), 404
    
    # Get unreturned books that are overdue
    current_date = datetime.strptime(sim_date, '%Y-%m-%d') if sim_date else datetime.utcnow()
    
    borrows = BookBorrow.query.filter(
        BookBorrow.student_id == student.id,
        BookBorrow.fine_paid == False
    ).all()
    
    fines = []
    for b in borrows:
        # Calculate fine for unreturned books
        if not b.return_date and current_date > b.due_date:
            days_overdue = (current_date - b.due_date).days
            b.fine_amount = days_overdue
            db.session.commit()
        
        # Include if has fine
        if b.fine_amount > 0:
            fines.append({
                'id': b.id,
                'book_title': b.book.title,
                'due_date': b.due_date.isoformat() + 'Z',
                'days_overdue': (current_date - b.due_date).days if current_date > b.due_date else 0,
                'fine_amount': b.fine_amount
            })
    
    return jsonify({
        'success': True,
        'fines': fines
    })

@api_bp.route('/library/pay-fine', methods=['POST'])
def pay_library_fine():
    """Pay a library fine"""
    data = request.get_json()
    borrow_id = data.get('borrow_id')
    
    if not borrow_id:
        return jsonify({'success': False, 'error': 'Borrow ID required'}), 400
    
    borrow = BookBorrow.query.get(borrow_id)
    if not borrow:
        return jsonify({'success': False, 'error': 'Borrow record not found'}), 404
    
    borrow.fine_paid = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Fine paid successfully'
    })


# ============== LABS ENDPOINTS ==============
def init_lab_apparatus():
    """Initialize lab apparatus from JSON if not already in database"""
    if Apparatus.query.count() == 0:
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'apparatus_data.json')
        if os.path.exists(data_path):
            with open(data_path, 'r') as f:
                apparatus_data = json.load(f)
                for item in apparatus_data:
                    apparatus = Apparatus(
                        name=item['name'],
                        category=item['category'],
                        quantity=item.get('quantity', 1),
                        quantity_available=item.get('quantity', 1),
                        damage_fine=item.get('damage_fine', 0)
                    )
                    db.session.add(apparatus)
                db.session.commit()

@api_bp.route('/labs/apparatus', methods=['GET'])
def get_lab_apparatus():
    """Get all lab apparatus"""
    init_lab_apparatus()
    apparatus = Apparatus.query.order_by(Apparatus.category, Apparatus.name).all()
    return jsonify({
        'success': True,
        'apparatus': [a.to_dict() for a in apparatus],
        'count': len(apparatus)
    })

@api_bp.route('/labs/stats', methods=['GET'])
def get_labs_stats():
    """Get labs statistics"""
    init_lab_apparatus()
    
    # Students currently in lab
    inside_count = Student.query.filter_by(is_inside=True).count()
    
    total_apparatus = Apparatus.query.count()
    borrowed_count = ApparatusBorrow.query.filter_by(return_date=None).count()
    
    # Calculate pending damage fines
    pending_fines = db.session.query(db.func.sum(ApparatusBorrow.damage_fine)).filter(
        ApparatusBorrow.is_damaged == True,
        ApparatusBorrow.fine_paid == False
    ).scalar() or 0
    
    # Recent activity
    recent = ApparatusBorrow.query.order_by(ApparatusBorrow.borrow_date.desc()).limit(10).all()
    
    return jsonify({
        'success': True,
        'stats': {
            'inside_count': inside_count,
            'total_apparatus': total_apparatus,
            'borrowed_count': borrowed_count,
            'pending_fines': int(pending_fines)
        },
        'recent_activity': [b.to_dict() for b in recent]
    })

@api_bp.route('/labs/borrow', methods=['POST'])
def borrow_apparatus():
    """Borrow lab apparatus"""
    data = request.get_json()
    apparatus_id = data.get('apparatus_id')
    student_identifier = data.get('student_identifier')
    
    if not apparatus_id or not student_identifier:
        return jsonify({'success': False, 'error': 'Apparatus ID and student identifier required'}), 400
    
    # Find student
    student = Student.query.filter(
        (Student.roll_number == student_identifier) | (Student.rfid_uid == student_identifier.upper())
    ).first()
    
    if not student:
        return jsonify({'success': False, 'error': 'Student not found'}), 404
    
    # Find apparatus
    apparatus = Apparatus.query.get(apparatus_id)
    if not apparatus:
        return jsonify({'success': False, 'error': 'Apparatus not found'}), 404
    
    if apparatus.quantity_available <= 0:
        return jsonify({'success': False, 'error': 'Apparatus not available'}), 400
    
    # Create borrow record
    borrow = ApparatusBorrow(
        student_id=student.id,
        apparatus_id=apparatus.id
    )
    
    apparatus.quantity_available -= 1
    db.session.add(borrow)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'borrow': borrow.to_dict()
    })

@api_bp.route('/labs/return', methods=['POST'])
def return_apparatus():
    """Return lab apparatus"""
    data = request.get_json()
    borrow_id = data.get('borrow_id')
    is_damaged = data.get('is_damaged', False)
    
    if not borrow_id:
        return jsonify({'success': False, 'error': 'Borrow ID required'}), 400
    
    borrow = ApparatusBorrow.query.get(borrow_id)
    if not borrow:
        return jsonify({'success': False, 'error': 'Borrow record not found'}), 404
    
    if borrow.return_date:
        return jsonify({'success': False, 'error': 'Apparatus already returned'}), 400
    
    borrow.return_date = datetime.utcnow()
    borrow.is_damaged = is_damaged
    
    if is_damaged:
        borrow.damage_fine = borrow.apparatus.damage_fine
    
    borrow.apparatus.quantity_available += 1
    db.session.commit()
    
    return jsonify({
        'success': True,
        'damage_fine': borrow.damage_fine if is_damaged else 0
    })

@api_bp.route('/labs/borrowed', methods=['GET'])
def get_borrowed_apparatus():
    """Get borrowed apparatus for a student"""
    student_identifier = request.args.get('student_identifier')
    
    if not student_identifier:
        return jsonify({'success': False, 'error': 'Student identifier required'}), 400
    
    student = Student.query.filter(
        (Student.roll_number == student_identifier) | (Student.rfid_uid == student_identifier.upper())
    ).first()
    
    if not student:
        return jsonify({'success': False, 'error': 'Student not found'}), 404
    
    borrows = ApparatusBorrow.query.filter_by(
        student_id=student.id,
        return_date=None
    ).order_by(ApparatusBorrow.borrow_date.desc()).all()
    
    return jsonify({
        'success': True,
        'borrows': [b.to_dict() for b in borrows]
    })

@api_bp.route('/labs/fines', methods=['GET'])
def get_lab_fines():
    """Get outstanding damage fines for a student"""
    student_identifier = request.args.get('student_identifier')
    
    if not student_identifier:
        return jsonify({'success': False, 'error': 'Student identifier required'}), 400
    
    student = Student.query.filter(
        (Student.roll_number == student_identifier) | (Student.rfid_uid == student_identifier.upper())
    ).first()
    
    if not student:
        return jsonify({'success': False, 'error': 'Student not found'}), 404
    
    borrows = ApparatusBorrow.query.filter(
        ApparatusBorrow.student_id == student.id,
        ApparatusBorrow.is_damaged == True,
        ApparatusBorrow.fine_paid == False
    ).all()
    
    fines = [{
        'id': b.id,
        'apparatus_name': b.apparatus.name,
        'return_date': b.return_date.isoformat() + 'Z' if b.return_date else None,
        'damage_fine': b.damage_fine
    } for b in borrows]
    
    return jsonify({
        'success': True,
        'fines': fines
    })

@api_bp.route('/labs/pay-fine', methods=['POST'])
def pay_lab_fine():
    """Pay a lab damage fine"""
    data = request.get_json()
    borrow_id = data.get('borrow_id')
    
    if not borrow_id:
        return jsonify({'success': False, 'error': 'Borrow ID required'}), 400
    
    borrow = ApparatusBorrow.query.get(borrow_id)
    if not borrow:
        return jsonify({'success': False, 'error': 'Borrow record not found'}), 404
    
    borrow.fine_paid = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Fine paid successfully'
    })

