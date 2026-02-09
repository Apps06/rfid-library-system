from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Admin

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    """Portal selection page"""
    return render_template('portal.html')

# ============== CLASSROOM ROUTES ==============
@views_bp.route('/classroom')
@views_bp.route('/classroom/dashboard')
def classroom_dashboard():
    """Classroom dashboard page"""
    return render_template('classroom/dashboard.html')

@views_bp.route('/classroom/students')
def classroom_students():
    """Classroom student management page"""
    return render_template('classroom/students.html')

@views_bp.route('/classroom/attendance')
def classroom_attendance():
    """Classroom attendance logs page"""
    return render_template('classroom/attendance.html')

@views_bp.route('/classroom/register')
def classroom_register():
    """Register new student with RFID"""
    return render_template('classroom/register.html')

# ============== LIBRARY ROUTES ==============
@views_bp.route('/library')
@views_bp.route('/library/dashboard')
def library_dashboard():
    """Library dashboard page"""
    return render_template('library/dashboard.html')

@views_bp.route('/library/attendance')
def library_attendance():
    """Library attendance page with RFID scanning"""
    return render_template('library/attendance.html')

@views_bp.route('/library/borrow')
def library_borrow():
    """Library book borrowing page"""
    return render_template('library/borrow.html')

@views_bp.route('/library/mybooks')
def library_mybooks():
    """Library - my borrowed books page"""
    return render_template('library/mybooks.html')

@views_bp.route('/library/payfine')
def library_payfine():
    """Library - pay fine page"""
    return render_template('library/payfine.html')

@views_bp.route('/library/register')
def library_register():
    """Library - register new student"""
    return render_template('library/register.html')

# ============== LABS ROUTES ==============
@views_bp.route('/labs')
@views_bp.route('/labs/dashboard')
def labs_dashboard():
    """Labs dashboard page"""
    return render_template('labs/dashboard.html')

@views_bp.route('/labs/attendance')
def labs_attendance():
    """Labs attendance page"""
    return render_template('labs/attendance.html')

@views_bp.route('/labs/borrow')
def labs_borrow():
    """Labs apparatus borrowing page"""
    return render_template('labs/borrow.html')

@views_bp.route('/labs/payfine')
def labs_payfine():
    """Labs - pay fine page"""
    return render_template('labs/payfine.html')

@views_bp.route('/labs/register')
def labs_register():
    """Labs - register new student"""
    return render_template('labs/register.html')

# ============== AUTH ROUTES ==============
@views_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            login_user(admin)
            return redirect(url_for('views.index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@views_bp.route('/logout')
@login_required
def logout():
    """Logout admin"""
    logout_user()
    return redirect(url_for('views.login'))
