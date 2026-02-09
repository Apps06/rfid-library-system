from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from app import db
from app.models import Student, AttendanceLog, Admin

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
    
    # Create attendance log
    log = AttendanceLog(
        student_id=student.id,
        rfid_uid=rfid_uid,
        action=action,
        device_id=device_id
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
