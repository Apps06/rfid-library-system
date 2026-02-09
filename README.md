<<<<<<< HEAD
# Student Library Logger - RFID + Raspberry Pi

An automated student library attendance tracking system using RFID technology and Raspberry Pi.

## 🎯 Features

- **Automated Check-in/Check-out**: Students scan RFID cards for instant entry/exit logging
- **Real-time Dashboard**: Live attendance stats and activity feed
- **Student Management**: Add, edit, and manage student records
- **Attendance Reports**: View and export attendance logs with date filtering
- **Offline Support**: Pi queues scans when disconnected, syncs when online
- **LED Feedback**: Visual indicators for entry (green), exit (yellow), and errors (red)

## 🏗️ Architecture

```
┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
│  Raspberry Pi   │  HTTP  │   Flask Web     │        │    PostgreSQL   │
│  + RFID Reader  │ ────── │   Application   │ ────── │    Database     │
│  + LED/Buzzer   │  POST  │   (Cloud/Local) │        │                 │
└─────────────────┘        └─────────────────┘        └─────────────────┘
```

## 📁 Project Structure

```
CPS_SEE/
├── app/                      # Flask Web Application
│   ├── __init__.py          # App factory
│   ├── models/              # Database models
│   │   ├── student.py       # Student model
│   │   ├── attendance.py    # Attendance logs
│   │   └── admin.py         # Admin authentication
│   ├── routes/              # API & View routes
│   │   ├── api.py           # REST API endpoints
│   │   └── views.py         # Web page routes
│   ├── static/              # CSS, JS assets
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── templates/           # HTML templates
│       ├── dashboard.html
│       ├── students.html
│       ├── attendance.html
│       └── register.html
├── raspberry_pi/            # Raspberry Pi Scanner
│   ├── rfid_scanner.py      # Main scanner script
│   ├── config.py            # Configuration
│   ├── requirements.txt     # Pi dependencies
│   └── setup_guide.md       # Hardware setup guide
├── run.py                   # Application entry point
├── config.py                # Flask configuration
├── requirements.txt         # Web app dependencies
└── README.md                # This file
```

## 🚀 Quick Start

### 1. Clone/Setup Project

```bash
cd d:\Documents\College\EL\CPS_SEE
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create `.env` file (copy from `.env.example`):
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://postgres:password@localhost:5432/library_logger
```

### 5. Initialize Database

```bash
# PostgreSQL: Create database first
# CREATE DATABASE library_logger;

python run.py
# Flask will auto-create tables on first run
```

### 6. Access Web App

Open http://localhost:5000 in your browser.

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scan` | POST | Log RFID scan (entry/exit) |
| `/api/students` | GET, POST | List/Create students |
| `/api/students/<id>` | GET, PUT, DELETE | Manage student |
| `/api/attendance` | GET | Get attendance logs |
| `/api/attendance/today` | GET | Today's attendance |
| `/api/dashboard/stats` | GET | Dashboard statistics |

### Scan Endpoint Example

```bash
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"rfid_uid": "ABC123"}'
```

Response:
```json
{
  "success": true,
  "action": "ENTRY",
  "student": {
    "name": "John Doe",
    "roll_number": "2024CS001"
  },
  "timestamp": "2026-02-06T17:30:00"
}
```

## 🔧 Raspberry Pi Setup

See [raspberry_pi/setup_guide.md](raspberry_pi/setup_guide.md) for detailed hardware wiring and software setup instructions.

**Quick Summary:**
1. Connect RC522 RFID reader via SPI
2. Connect LEDs to GPIO 17, 22, 27
3. Enable SPI: `sudo raspi-config`
4. Install dependencies: `pip3 install -r raspberry_pi/requirements.txt`
5. Configure API URL in `raspberry_pi/config.py`
6. Run: `python3 raspberry_pi/rfid_scanner.py`

## 🌐 Deployment Options

### Local Development
```bash
python run.py
```

### Production (Free Hosting)

**Render.com:**
1. Push to GitHub
2. Create new Web Service on Render
3. Set environment variables
4. Deploy!

**Railway.app:**
1. Connect GitHub repo
2. Add PostgreSQL plugin
3. Deploy automatically

## 👥 Team

Cyber Physical Systems Project - Final Exam

## 📄 License

MIT License - Free for educational use
=======
# rfid-library-system
Automated RFID-based library management system
>>>>>>> 84f28eaf59e40c79681bac423b9a0a8f6e7cf2e2
