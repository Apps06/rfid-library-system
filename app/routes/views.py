from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Admin

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    """Redirect to dashboard"""
    return redirect(url_for('views.dashboard'))

@views_bp.route('/dashboard')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@views_bp.route('/students')
def students():
    """Student management page"""
    return render_template('students.html')

@views_bp.route('/attendance')
def attendance():
    """Attendance logs page"""
    return render_template('attendance.html')

@views_bp.route('/register')
def register():
    """Register new student with RFID"""
    return render_template('register.html')

@views_bp.route('/station')
def station():
    """Zone selection station page"""
    return render_template('station.html')

@views_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            login_user(admin)
            return redirect(url_for('views.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@views_bp.route('/logout')
@login_required
def logout():
    """Logout admin"""
    logout_user()
    return redirect(url_for('views.login'))
