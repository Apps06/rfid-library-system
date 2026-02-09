from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from app import db
from app.models import Student, AttendanceLog, Admin, Book, BorrowRecord

api_bp = Blueprint('api', __name__)

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
    zone = data.get('zone', 'Library')
    
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
    
    # Zone-specific toggling logic
    latest_log = AttendanceLog.query.filter_by(
        student_id=student.id, 
        zone=zone
    ).order_by(AttendanceLog.timestamp.desc()).first()

    if latest_log and latest_log.action == 'ENTRY':
        action = 'EXIT'
        # Update student global state if needed
        student.is_inside = False
    else:
        action = 'ENTRY'
        student.is_inside = True
    
    # Create attendance log
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
        'student': {
            'id': student.id,
            'name': student.name,
            'roll_number': student.roll_number,
            'department': student.department
        },
        'zone': log.zone,
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
    """Delete a student"""
    student = Student.query.get_or_404(id)
    
    # Delete related attendance logs first
    AttendanceLog.query.filter_by(student_id=id).delete()
    
    db.session.delete(student)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Student deleted'})


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
    """Get today's attendance logs"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    logs = AttendanceLog.query.filter(
        AttendanceLog.timestamp >= today,
        AttendanceLog.timestamp < tomorrow
    ).order_by(AttendanceLog.timestamp.desc()).all()
    
    return jsonify({
        'success': True,
        'logs': [log.to_dict() for log in logs],
        'count': len(logs)
    })


@api_bp.route('/attendance/<int:id>/zone', methods=['PUT'])
def update_attendance_zone(id):
    """Update the zone for a specific attendance log"""
    log = AttendanceLog.query.get_or_404(id)
    data = request.get_json()
    
    if not data or 'zone' not in data:
        return jsonify({'success': False, 'error': 'Zone required'}), 400
    
    log.zone = data['zone']
    db.session.commit()
    
    return jsonify({
        'success': True,
        'log': log.to_dict()
    })


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


# ============== LIBRARY BOOK ENDPOINTS ==============
@api_bp.route('/books', methods=['GET'])
def get_books():
    """List all books with availability"""
    search = request.args.get('search', '').strip()
    query = Book.query
    
    if search:
        query = query.filter(
            (Book.title.ilike(f'%{search}%')) | 
            (Book.author.ilike(f'%{search}%')) |
            (Book.isbn.ilike(f'%{search}%'))
        )
        
    books = query.all()
    return jsonify({
        'success': True,
        'books': [b.to_dict() for b in books]
    })

@api_bp.route('/borrow', methods=['GET'])
def get_student_borrows():
    """Get active/overdue borrows for a student"""
    student_id = request.args.get('student_id')
    if not student_id:
        return jsonify({'success': False, 'error': 'student_id required'}), 400
        
    borrows = BorrowRecord.query.filter_by(
        student_id=student_id,
        returned_at=None
    ).all()
    
    return jsonify({
        'success': True,
        'borrows': [b.to_dict() for b in borrows]
    })

@api_bp.route('/borrow', methods=['POST'])
def borrow_book():
    """Borrow a book"""
    try:
        data = request.get_json()
        print(f"📥 Borrow attempt: {data}")
        
        if not data or 'book_id' not in data or 'student_id' not in data:
            return jsonify({'success': False, 'error': 'book_id and student_id required'}), 400
            
        book = Book.query.get(data['book_id'])
        if not book:
            return jsonify({'success': False, 'error': 'Book not found'}), 404
            
        if book.available_copies <= 0:
            return jsonify({'success': False, 'error': 'No copies available'}), 400
            
        # Check if student already has this book borrowed
        existing = BorrowRecord.query.filter_by(
            student_id=data['student_id'],
            book_id=data['book_id'],
            returned_at=None
        ).first()
        
        if existing:
            return jsonify({'success': False, 'error': 'You already have this book borrowed'}), 400
            
        # Create borrow record
        borrow = BorrowRecord(
            book_id=book.id,
            student_id=data['student_id']
        )
        
        book.available_copies -= 1
        db.session.add(borrow)
        db.session.commit()
        
        print(f"✅ Borrow successful: {borrow.id}")
        return jsonify({
            'success': True,
            'borrow': borrow.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"❌ Borrow error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/borrow/<int:id>/extend', methods=['PUT'])
def extend_borrow(id):
    """Extend borrow deadline (max 2 times, blocked for important)"""
    borrow = BorrowRecord.query.get_or_404(id)
    
    if borrow.returned_at:
        return jsonify({'success': False, 'error': 'Book already returned'}), 400
        
    if borrow.book.is_important:
        return jsonify({'success': False, 'error': 'This book is marked as IMPORTANT and cannot be extended'}), 403
        
    if borrow.extensions_used >= 2:
        return jsonify({'success': False, 'error': 'Maximum 2 extensions reached. Manual approval required.'}), 403
        
    # NEW RULE: Cannot extend again until the previous due date has passed
    # If extended Once: Cannot extend again until "original" due date (current - 7 days) is passed
    if borrow.extensions_used > 0:
        previous_due_date = borrow.due_date - timedelta(days=7)
        if datetime.utcnow() < previous_due_date:
            return jsonify({
                'success': False, 
                'error': f'Cannot extend again yet. Please wait until {previous_due_date.strftime("%b %d")} (your previous due date) has passed.'
            }), 403
            
    # Extend by 7 days and snap to end of day
    new_due_date = borrow.due_date + timedelta(days=7)
    borrow.due_date = new_due_date.replace(hour=23, minute=59, second=59, microsecond=0)
    borrow.extensions_used += 1
    db.session.commit()
    
    return jsonify({
        'success': True,
        'borrow': borrow.to_dict(),
        'message': f'Extended by 7 days. Extensions used: {borrow.extensions_used}/2'
    })

@api_bp.route('/borrow/<int:id>/return', methods=['PUT'])
def return_book(id):
    """Return a borrowed book"""
    borrow = BorrowRecord.query.get_or_404(id)
    
    if borrow.returned_at:
        return jsonify({'success': False, 'error': 'Book already returned'}), 400
        
    borrow.returned_at = datetime.utcnow()
    borrow.status = 'RETURNED'
    borrow.book.available_copies += 1
    
    # Calculate final fine
    borrow.calculate_fine()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'borrow': borrow.to_dict()
    })

@api_bp.route('/fines/<int:id>/pay', methods=['POST'])
def pay_fine(id):
    """Mark fine as paid"""
    borrow = BorrowRecord.query.get_or_404(id)
    
    if borrow.fine_paid:
        return jsonify({'success': False, 'error': 'Fine already paid'}), 400
        
    borrow.fine_paid = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Payment successful'
    })
