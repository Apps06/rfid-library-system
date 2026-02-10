# 📚 RVCE Campus Portal — RFID-Based Multi-Module Management System

> A Cyber-Physical System (CPS) for managing **Classroom Attendance**, **Library Book Borrowing**, and **Laboratory Apparatus Tracking** using RFID technology, powered by a Raspberry Pi and a Flask web application.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat&logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?style=flat&logo=postgresql&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-3B+-C51A4A?style=flat&logo=raspberrypi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## 📖 Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Hardware Components](#hardware-components)
- [Software Stack](#software-stack)
- [Features](#features)
  - [Portal Selection](#portal-selection)
  - [Classroom Module](#classroom-module)
  - [Library Module](#library-module)
  - [Labs Module](#labs-module)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
  - [Web Server Setup](#1-web-server-setup)
  - [Raspberry Pi Setup](#2-raspberry-pi-setup)
  - [Hardware Wiring](#3-hardware-wiring)
- [Deployment](#deployment)
- [Usage Guide](#usage-guide)
- [Technologies Used](#technologies-used)
- [Contributors](#contributors)
- [License](#license)

---

## Overview

The **RVCE Campus Portal** is a Cyber-Physical System (CPS) that bridges physical RFID card scanning with a cloud-hosted web application to automate and digitize campus operations across three key domains:

| Module | Purpose |
|--------|---------|
| **Classroom** | RFID-based student attendance logging with entry/exit tracking |
| **Library** | Book borrowing, renewal, return management with automated overdue fine calculation |
| **Labs** | Laboratory apparatus borrowing/returning with damage tracking and fine management |

The system uses **RFID-RC522** readers connected to a **Raspberry Pi 3 B+** to scan student ID cards. Each scan is transmitted over the network to the Flask web server, which processes the data, updates the database, and presents real-time information through an interactive web dashboard.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RVCE Campus Portal                          │
│                     System Architecture Diagram                     │
└─────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────┐          HTTPS / HTTP
  │   Raspberry Pi 3 B+  │ ──────────────────────────┐
  │  ┌────────────────┐  │                            │
  │  │  RFID-RC522    │  │     ┌─────────────────┐    │
  │  │  (SPI Bus)     │  │     │                 │    ▼
  │  └────────────────┘  │     │   Flask Web     │ ┌──────────────┐
  │  ┌────────────────┐  │     │   Application   │ │              │
  │  │  LED Feedback  │  │     │   (Server)      │ │  PostgreSQL  │
  │  │  🟢 Entry      │  │     │                 │ │  Database    │
  │  │  🟡 Exit       │  │     │  ┌───────────┐  │ │              │
  │  │  🔴 Error      │  │     │  │ REST API  │◄─┤─┤  - students  │
  │  └────────────────┘  │     │  └───────────┘  │ │  - attendance│
  │  ┌────────────────┐  │     │  ┌───────────┐  │ │  - books     │
  │  │  Buzzer (opt.) │  │     │  │ Templates │  │ │  - borrows   │
  │  │  🔊 Beep       │  │     │  │ (Jinja2)  │  │ │  - apparatus │
  │  └────────────────┘  │     │  └───────────┘  │ │  - fines     │
  │  ┌────────────────┐  │     │                 │ │              │
  │  │  Offline Queue │  │     └─────────────────┘ └──────────────┘
  │  │  (SQLite)      │  │            ▲
  │  └────────────────┘  │            │
  └──────────────────────┘    ┌───────┴────────┐
                              │  Web Browser   │
        RFID Card             │  Dashboard UI  │
     ┌───────────┐            │  (HTML/CSS/JS) │
     │ Student   │            └────────────────┘
     │ ID Card   │
     └───────────┘
```

### Data Flow

1. **Student taps RFID card** on the RC522 reader connected to the Raspberry Pi.
2. **Raspberry Pi reads the card UID** via SPI and sends an HTTP POST request to `/api/scan` with the UID and zone identifier.
3. **Flask API processes the scan**: looks up the student, toggles their entry/exit state, logs the attendance with the zone (Classroom/Library/Lab), and returns the result.
4. **Raspberry Pi provides physical feedback**: Green LED for entry, Yellow LED for exit, Red LED for errors, with audible buzzer confirmation.
5. **If the network is unavailable**, scans are queued in a local SQLite database on the Pi and retried automatically when connectivity is restored.
6. **Web dashboard** displays real-time statistics, attendance logs, and management tools accessible from any browser.

---

## Hardware Components

### Bill of Materials

| # | Component | Specification | Qty | Purpose |
|---|-----------|---------------|-----|---------|
| 1 | **Raspberry Pi 3 Model B+** | 1.4 GHz Quad-Core, 1 GB RAM | 1 | Main controller and processing unit |
| 2 | **RFID-RC522 Module** | 13.56 MHz, MIFARE compatible | 1 | Contactless RFID card reader |
| 3 | **MIFARE Classic 1K Cards** | ISO 14443A, 13.56 MHz | 2+ | Student identification cards |
| 4 | **Green LED** | 5 mm, 20 mA | 1 | Entry/success indicator |
| 5 | **Yellow LED** | 5 mm, 20 mA | 1 | Exit indicator |
| 6 | **Red LED** | 5 mm, 20 mA | 1 | Error indicator |
| 7 | **220Ω Resistors** | 1/4W carbon film | 3 | Current limiting for LEDs |
| 8 | **Active Buzzer** | 5V, 2300 Hz (optional) | 1 | Audible scan confirmation |
| 9 | **Breadboard** | 830 tie-points | 1 | Prototyping connections |
| 10 | **Jumper Wires** | Male-to-Female | ~15 | Component interconnections |
| 11 | **MicroSD Card** | 16 GB+ Class 10 | 1 | Raspberry Pi OS storage |
| 12 | **5V USB Power Supply** | 2.5A Micro-USB | 1 | Raspberry Pi power |

### Wiring Diagram

#### RFID-RC522 → Raspberry Pi GPIO

| RC522 Pin | Raspberry Pi Pin | GPIO Number | Description |
|-----------|------------------|-------------|-------------|
| **SDA** | Pin 24 | GPIO 8 (CE0) | SPI Chip Select |
| **SCK** | Pin 23 | GPIO 11 (SCLK) | SPI Clock |
| **MOSI** | Pin 19 | GPIO 10 (MOSI) | SPI Master Out Slave In |
| **MISO** | Pin 21 | GPIO 9 (MISO) | SPI Master In Slave Out |
| **IRQ** | — | Not Connected | Interrupt (unused) |
| **GND** | Pin 6 | Ground | Ground reference |
| **RST** | Pin 22 | GPIO 25 | Reset |
| **3.3V** | Pin 1 | 3.3V Power | ⚠️ Must be 3.3V, NOT 5V |

#### LED & Buzzer Connections

| Component | GPIO Pin | Raspberry Pi Pin | Circuit |
|-----------|----------|------------------|---------|
| 🟢 Green LED | GPIO 17 | Pin 11 | GPIO → 220Ω → LED(+) → GND |
| 🟡 Yellow LED | GPIO 22 | Pin 15 | GPIO → 220Ω → LED(+) → GND |
| 🔴 Red LED | GPIO 27 | Pin 13 | GPIO → 220Ω → LED(+) → GND |
| 🔊 Buzzer | GPIO 18 | Pin 12 | GPIO → Buzzer(+), GND → Buzzer(-) |

#### Visual Pin Reference

```
Raspberry Pi GPIO Header (Top View)
┌──────────────────────────────────────┐
│ [3.3V]  1 ●  ○ 2  [5V]              │  ● = Used
│ [GPIO2] 3 ○  ○ 4  [5V]              │  ○ = Unused
│ [GPIO3] 5 ○  ● 6  [GND] ← RC522    │
│ [GPIO4] 7 ○  ○ 8  [GPIO14]          │
│ [GND]   9 ○  ○ 10 [GPIO15]          │
│ [GPIO17]11 ●  ● 12 [GPIO18] ← BUZZ  │  ← GREEN LED
│ [GPIO27]13 ●  ○ 14 [GND]            │  ← RED LED
│ [GPIO22]15 ●  ○ 16 [GPIO23]         │  ← YELLOW LED
│ [3.3V] 17 ○  ○ 18 [GPIO24]          │
│ [MOSI] 19 ●  ○ 20 [GND]            │  ← RC522
│ [MISO] 21 ●  ● 22 [GPIO25]         │  ← RC522
│ [SCLK] 23 ●  ● 24 [CE0]            │  ← RC522
│ [GND]  25 ○  ○ 26 [CE1]            │
└──────────────────────────────────────┘
```

---

## Software Stack

### Web Application (Server)

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.10+ | Primary programming language |
| **Flask** | 3.0.0 | Lightweight WSGI web framework |
| **Flask-SQLAlchemy** | 3.1.1 | ORM for database operations |
| **Flask-Login** | 0.6.3 | Session-based admin authentication |
| **Flask-CORS** | 4.0.0 | Cross-Origin Resource Sharing support |
| **PostgreSQL** | 15+ | Production relational database |
| **SQLite** | 3 | Development/fallback database |
| **psycopg2-binary** | 2.9.9 | PostgreSQL adapter for Python |
| **Werkzeug** | 3.0.1 | WSGI utilities and password hashing |
| **Gunicorn** | 21.2.0 | Production WSGI HTTP server |
| **python-dotenv** | 1.0.0 | Environment variable management |
| **Jinja2** | — | Server-side HTML templating (bundled with Flask) |

### Frontend

| Technology | Purpose |
|------------|---------|
| **HTML5** | Semantic page structure |
| **CSS3** | Custom dark theme with module-specific accent colors |
| **Vanilla JavaScript** | DOM manipulation, API communication, dynamic UI updates |
| **Google Fonts (Inter)** | Modern typography |

### Raspberry Pi (Client)

| Technology | Version | Purpose |
|------------|---------|---------|
| **Raspberry Pi OS** | Bullseye/Bookworm | Operating system |
| **Python 3** | 3.9+ | Scanner script runtime |
| **mfrc522** | — | RFID-RC522 reader library |
| **RPi.GPIO** | — | GPIO pin control for LEDs and buzzer |
| **requests** | — | HTTP client for API communication |
| **SQLite 3** | — | Local offline scan queue |
| **SPI (spidev)** | — | Serial Peripheral Interface for RC522 |
| **systemd** | — | Service management for auto-start on boot |

### Communication Protocols

| Protocol | Usage |
|----------|-------|
| **SPI** | Raspberry Pi ↔ RFID-RC522 reader communication |
| **HTTP/HTTPS** | Raspberry Pi ↔ Flask server REST API |
| **TCP/IP** | Network transport layer |
| **ISO 14443A** | RFID card communication standard (13.56 MHz) |

---

## Features

### Portal Selection

The root URL (`/`) presents a visually striking portal page with three module cards. Each card has a distinct color theme and icon, providing clear navigation to:

- 🏫 **Classroom** — Magenta/pink accent
- 📚 **Library** — Cyan/blue accent
- 🔬 **Labs** — Orange/red accent

### Classroom Module

| Feature | Description |
|---------|-------------|
| **RFID Attendance** | Scan student cards to log entry/exit with timestamps |
| **Auto-Registration** | Unknown cards are auto-registered with temporary details, then redirected to the registration form |
| **Student Management** | View, search, edit, and delete registered students |
| **Attendance Logs** | Filterable attendance history with pagination |
| **Dashboard** | Real-time stats — students inside, total registered, today's entries/exits |
| **CSV Export** | Download attendance logs as CSV files filtered by zone |

### Library Module

| Feature | Description |
|---------|-------------|
| **Book Catalogue** | 20 pre-loaded books across categories (CS, Physics, Math, Chemistry, Literature) |
| **Book Borrowing** | Borrow books with 14-day loan period, tracked by student ID/RFID |
| **Renewal System** | Extend due date by 14 days, maximum 2 renewals per borrow |
| **Important Books** | Flagged books (e.g., reference texts) cannot be renewed/reissued |
| **Overdue Fines** | Automated ₹1/day fine calculation for overdue books |
| **Fine Payment** | Simulated QR-code-based payment interface |
| **Date Simulation** | Configurable simulation date to test fine accumulation without waiting |
| **RFID Attendance** | Track who enters/exits the library |
| **CSV Export** | Export library attendance as CSV |

### Labs Module

| Feature | Description |
|---------|-------------|
| **Apparatus Catalogue** | 15 pre-loaded items (Microscopes, Beakers, Oscilloscopes, Multimeters, etc.) |
| **Equipment Borrowing** | Borrow lab apparatus tracked by student ID/RFID |
| **Return with Damage Report** | Return apparatus with option to flag as damaged |
| **Damage Fines** | One-time fine applied when apparatus is returned damaged (₹200–₹5000 depending on item) |
| **Fine Payment** | Simulated QR-code-based payment interface |
| **RFID Attendance** | Track who enters/exits the lab |
| **CSV Export** | Export lab attendance as CSV |

### Cross-Module Features

| Feature | Description |
|---------|-------------|
| **Global Student Registry** | Students register once and are recognized across all modules |
| **Zone-Based Attendance** | Each module tracks attendance separately (Library, Lab, Classroom zones) |
| **Auto-Registration Flow** | Scanning an unknown card triggers registration, then redirects back to the originating zone |
| **Offline Resilience** | Raspberry Pi queues scans locally when the server is unreachable, auto-syncs when connectivity returns |
| **Admin Authentication** | Secure admin login with bcrypt password hashing |

---

## Database Schema

```
┌──────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│     students     │     │   attendance_logs     │     │      books       │
├──────────────────┤     ├──────────────────────┤     ├──────────────────┤
│ id (PK)          │◄────│ student_id (FK)       │     │ id (PK)          │
│ rfid_uid (UQ)    │     │ id (PK)               │     │ title            │
│ name             │     │ rfid_uid              │     │ author           │
│ roll_number (UQ) │     │ action (ENTRY/EXIT)   │     │ isbn (UQ)        │
│ department       │     │ timestamp             │     │ is_important     │
│ email            │     │ device_id             │     │ quantity         │
│ is_active        │     │ zone                  │     │ quantity_available│
│ is_inside        │     └──────────────────────┘     │ created_at       │
│ created_at       │                                   └────────┬─────────┘
└───────┬──────────┘                                            │
        │                                                       │
        │         ┌──────────────────────┐                      │
        │         │    book_borrows      │                      │
        ├────────►│ id (PK)              │◄─────────────────────┘
        │         │ student_id (FK)      │
        │         │ book_id (FK)         │
        │         │ borrow_date          │
        │         │ due_date             │
        │         │ return_date          │
        │         │ renewal_count        │
        │         │ fine_amount          │
        │         │ fine_paid            │
        │         └──────────────────────┘
        │
        │         ┌──────────────────────┐     ┌──────────────────┐
        │         │  apparatus_borrows   │     │    apparatus      │
        └────────►│ id (PK)              │◄────│ id (PK)          │
                  │ student_id (FK)      │     │ name             │
                  │ apparatus_id (FK)    │     │ category         │
                  │ borrow_date          │     │ quantity         │
                  │ return_date          │     │ quantity_available│
                  │ is_damaged           │     │ damage_fine      │
                  │ damage_fine          │     │ created_at       │
                  │ fine_paid            │     └──────────────────┘
                  └──────────────────────┘

┌──────────────────┐
│     admins       │
├──────────────────┤
│ id (PK)          │
│ username (UQ)    │
│ password_hash    │
│ created_at       │
└──────────────────┘
```

### Model Summary

| Model | Table | Records | Description |
|-------|-------|---------|-------------|
| `Student` | `students` | Dynamic | Globally registered students with RFID UIDs |
| `AttendanceLog` | `attendance_logs` | Dynamic | Zone-aware entry/exit logs with timestamps |
| `Book` | `books` | 20 (pre-loaded) | Library book catalogue |
| `BookBorrow` | `book_borrows` | Dynamic | Book lending records with fines |
| `Apparatus` | `apparatus` | 15 (pre-loaded) | Lab equipment catalogue |
| `ApparatusBorrow` | `apparatus_borrows` | Dynamic | Equipment lending and damage records |
| `Admin` | `admins` | Manual | Administrator accounts |

---

## API Reference

All endpoints are prefixed with `/api`.

### RFID Scanning

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/scan` | Process RFID scan (accepts `rfid_uid`, `device_id`, `zone`) |

### Student Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/students` | List all registered students |
| `POST` | `/students` | Register a new student |
| `GET` | `/students/<id>` | Get student details |
| `PUT` | `/students/<id>` | Update student information |
| `DELETE` | `/students/<id>` | Delete a student |

### Attendance

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/attendance` | Get paginated attendance logs (filter by `date`) |
| `GET` | `/attendance/today` | Get today's logs (filter by `zone`) |
| `GET` | `/attendance/export` | Download CSV (filter by `zone`, `date`) |

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard/stats` | Aggregated statistics for classroom dashboard |

### Admin Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/admin/login` | Admin login |
| `POST` | `/admin/create` | Create admin account |

### Library

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/library/books` | Get all books |
| `GET` | `/library/stats` | Library statistics |
| `POST` | `/library/borrow` | Borrow a book |
| `POST` | `/library/return` | Return a book |
| `POST` | `/library/extend` | Renew/extend a borrow |
| `GET` | `/library/borrowed` | Get student's borrowed books |
| `GET` | `/library/fines` | Get student's outstanding fines |
| `POST` | `/library/pay-fine` | Pay a fine |

### Labs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/labs/apparatus` | Get all apparatus |
| `GET` | `/labs/stats` | Lab statistics |
| `POST` | `/labs/borrow` | Borrow apparatus |
| `POST` | `/labs/return` | Return apparatus (with optional `is_damaged` flag) |
| `GET` | `/labs/borrowed` | Get student's borrowed items |
| `GET` | `/labs/fines` | Get student's damage fines |
| `POST` | `/labs/pay-fine` | Pay a damage fine |

**Total: 25 API endpoints**

---

## Project Structure

```
rfid-library-system/
├── run.py                          # Application entry point
├── config.py                       # Flask configuration (DB URI, secret key)
├── requirements.txt                # Python dependencies (server)
├── migrate_zones.py                # Database migration script for zone column
├── .env                            # Environment variables (DATABASE_URL, SECRET_KEY)
├── .gitignore                      # Git ignore rules
├── LICENSE                         # MIT License
│
├── app/                            # Flask application package
│   ├── __init__.py                 # App factory, extension initialization
│   │
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── __init__.py             # Model imports
│   │   ├── student.py              # Student model
│   │   ├── attendance.py           # AttendanceLog model (with zone support)
│   │   ├── admin.py                # Admin model (bcrypt auth)
│   │   ├── book.py                 # Book & BookBorrow models
│   │   └── apparatus.py            # Apparatus & ApparatusBorrow models
│   │
│   ├── routes/                     # Route handlers
│   │   ├── api.py                  # REST API endpoints (25 endpoints)
│   │   └── views.py                # Page rendering routes
│   │
│   ├── data/                       # Static seed data
│   │   ├── books_data.json         # 20 library books with authors, ISBNs
│   │   └── apparatus_data.json     # 15 lab apparatus with categories, fines
│   │
│   ├── templates/                  # Jinja2 HTML templates
│   │   ├── portal.html             # Module selection landing page
│   │   ├── base.html               # Root base template
│   │   ├── login.html              # Admin login page
│   │   ├── register.html           # Student registration (root)
│   │   ├── dashboard.html          # Root dashboard
│   │   ├── students.html           # Student management
│   │   ├── attendance.html         # Attendance logs
│   │   │
│   │   ├── classroom/              # Classroom module templates
│   │   │   ├── base.html           # Classroom base (magenta theme)
│   │   │   ├── dashboard.html      # Classroom dashboard
│   │   │   ├── students.html       # Student management
│   │   │   ├── attendance.html     # Attendance logs + CSV export
│   │   │   └── register.html       # Student registration
│   │   │
│   │   ├── library/                # Library module templates
│   │   │   ├── base.html           # Library base (cyan theme + sim date)
│   │   │   ├── dashboard.html      # Library stats dashboard
│   │   │   ├── attendance.html     # Library RFID attendance + CSV export
│   │   │   ├── borrow.html         # Book borrowing interface
│   │   │   ├── mybooks.html        # View/extend/return borrowed books
│   │   │   ├── payfine.html        # Fine payment with QR simulation
│   │   │   └── register.html       # Student registration (Library zone)
│   │   │
│   │   └── labs/                   # Labs module templates
│   │       ├── base.html           # Labs base (orange theme)
│   │       ├── dashboard.html      # Lab stats dashboard
│   │       ├── attendance.html     # Lab RFID attendance + CSV export
│   │       ├── borrow.html         # Apparatus borrow/return + damage
│   │       ├── payfine.html        # Damage fine payment with QR simulation
│   │       └── register.html       # Student registration (Lab zone)
│   │
│   └── static/                     # Static assets
│       ├── css/
│       │   └── style.css           # Global styles (dark theme, 700+ lines)
│       └── js/
│           └── app.js              # Shared JS (API client, toasts, helpers)
│
└── raspberry_pi/                   # Raspberry Pi scanner package
    ├── rfid_scanner.py             # Main scanner script (337 lines)
    ├── config.py                   # Pi configuration (API URL, GPIO pins)
    ├── requirements.txt            # Pi Python dependencies
    └── setup_guide.md              # Hardware wiring and setup instructions
```

---

## Installation & Setup

### 1. Web Server Setup

```bash
# Clone the repository
git clone https://github.com/your-username/rfid-library-system.git
cd rfid-library-system

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your database URL and secret key:
#   DATABASE_URL=postgresql://user:password@localhost:5432/library_logger
#   SECRET_KEY=your-secret-key-here

# Run database migrations (if upgrading from older version)
python3 migrate_zones.py

# Start the development server
python3 run.py
# Server starts at http://localhost:5000
```

### 2. Raspberry Pi Setup

```bash
# Enable SPI interface
sudo raspi-config
# Navigate to: Interface Options → SPI → Enable
sudo reboot

# Install dependencies on the Pi
cd raspberry_pi
pip3 install -r requirements.txt

# Configure the API URL
nano config.py
# Set API_URL to your server address:
#   API_URL = "http://192.168.1.100:5000"     # Local network
#   API_URL = "https://your-app.onrender.com"  # Cloud

# Test the scanner
python3 rfid_scanner.py

# Enable auto-start on boot (optional)
sudo nano /etc/systemd/system/library-scanner.service
# Paste the systemd service configuration (see raspberry_pi/setup_guide.md)
sudo systemctl enable library-scanner
sudo systemctl start library-scanner
```

### 3. Hardware Wiring

Refer to the [Hardware Components](#hardware-components) section above for detailed wiring tables. Key points:

- ⚠️ **RC522 must be powered at 3.3V** — connecting to 5V will damage the module.
- Each LED requires a **220Ω resistor** in series.
- The buzzer is optional but recommended for audible feedback.
- Use **BCM numbering** for GPIO pins (matching `config.py`).

---

## Deployment

### Production Deployment (Gunicorn + PostgreSQL)

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb library_logger

# Run with Gunicorn (production WSGI server)
gunicorn --bind 0.0.0.0:5000 --workers 4 "app:create_app()"
```

### Cloud Deployment

The application is configured to work with cloud platforms:

- **Render** / **Railway** — Set `DATABASE_URL` environment variable to the PostgreSQL connection string.
- The `config.py` automatically handles `postgres://` → `postgresql://` URL translation for compatibility.

---

## Usage Guide

### First-Time Setup

1. **Start the server** and navigate to `http://localhost:5000`.
2. **Create an admin account** via the API:
   ```bash
   curl -X POST http://localhost:5000/api/admin/create \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "your-password"}'
   ```
3. **Access the portal** — you'll see three module cards.

### Typical Workflow

1. **Student scans RFID card** at a reader.
2. If **new card**: system auto-registers with temporary details → redirects to registration form → student fills in name, roll number, department → redirected back to the zone dashboard.
3. If **known student**: entry/exit is logged with the appropriate zone, LED flashes, buzzer beeps.
4. **Library**: Students can browse books, borrow (14-day period), renew (up to 2 times), return, and pay overdue fines.
5. **Labs**: Students can borrow apparatus, return with damage reporting, and pay damage fines.
6. **Admin**: Export attendance as CSV for any zone, manage students, view dashboards.

---

## Technologies Used

### Summary Table

| Layer | Technology | Role |
|-------|-----------|------|
| **Hardware** | Raspberry Pi 3 B+ | Edge computing device / RFID reader controller |
| **Hardware** | RFID-RC522 (MFRC522) | 13.56 MHz contactless card reader (SPI interface) |
| **Hardware** | MIFARE Classic 1K | ISO 14443A RFID cards for student identification |
| **Hardware** | LEDs (Green, Yellow, Red) | Visual scan feedback indicators |
| **Hardware** | Active Buzzer (5V) | Audible scan confirmation |
| **Protocol** | SPI | Communication between Raspberry Pi and RC522 |
| **Protocol** | REST/HTTP | API communication between Pi and server |
| **Protocol** | ISO 14443A | RFID card communication standard |
| **Backend** | Python 3.10+ | Server and scanner programming language |
| **Backend** | Flask 3.0 | Web framework |
| **Backend** | SQLAlchemy | Object-Relational Mapping |
| **Backend** | Jinja2 | Server-side templating |
| **Backend** | Gunicorn | Production WSGI server |
| **Database** | PostgreSQL 15+ | Production database |
| **Database** | SQLite 3 | Development DB / Pi offline queue |
| **Frontend** | HTML5 / CSS3 / JavaScript | UI rendering and interactivity |
| **Auth** | Flask-Login + bcrypt | Session management and password hashing |
| **DevOps** | systemd | Service management on Raspberry Pi |
| **DevOps** | python-dotenv | Environment configuration |

---

## Contributors

| Name | Role |
|------|------|
| | Project Development |

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built as a Cyber-Physical Systems project at <strong>RVCE</strong> 🎓
</p>
