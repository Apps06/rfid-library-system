#!/usr/bin/env python3
"""
RFID Library Logger - Raspberry Pi Scanner
==========================================
This script reads RFID cards using the RC522 module and sends
scan data to the cloud API. Includes LED feedback and offline queue.

Hardware Setup:
- RFID-RC522 connected via SPI
- Green LED on GPIO 17 (Entry indicator)
- Yellow LED on GPIO 22 (Exit indicator)
- Red LED on GPIO 27 (Error indicator)
- Optional: Buzzer on GPIO 18

Run with: python3 rfid_scanner.py
"""

import time
import signal
import sys
import sqlite3
import threading
import requests
from datetime import datetime

# Raspberry Pi specific imports
try:
    import RPi.GPIO as GPIO
    from mfrc522 import SimpleMFRC522
    PI_MODE = True
except ImportError as e:
    PI_MODE = False
    print(f"📟  Running in USB/Manual RFID mode (Pi hardware not detected or library missing: {e})")
    print("    → Connect a USB RFID reader or type UIDs manually")
except Exception as e:
    PI_MODE = False
    print(f"⚠️  Hardware initialization failed: {e}")
    print("    → Falling back to USB/Manual mode")

# Local config
from config import (
    API_URL, SCAN_ENDPOINT, DEVICE_ID,
    LED_GREEN, LED_RED, LED_YELLOW, BUZZER_PIN,
    SCAN_DELAY, LED_DURATION, BEEP_DURATION, RETRY_INTERVAL
)

import os

# SimpleMFRC522 sets GPIO.BOARD mode internally, so we must convert
# our BCM pin numbers to BOARD numbering to avoid a mode conflict.
if PI_MODE:
    _BCM_TO_BOARD = {17: 11, 27: 13, 22: 15, 18: 12}
    LED_GREEN = _BCM_TO_BOARD.get(LED_GREEN, LED_GREEN)
    LED_YELLOW = _BCM_TO_BOARD.get(LED_YELLOW, LED_YELLOW)
    LED_RED = _BCM_TO_BOARD.get(LED_RED, LED_RED)
    BUZZER_PIN = _BCM_TO_BOARD.get(BUZZER_PIN, BUZZER_PIN)
    print(f"   📌 Pins converted to BOARD mode: G={LED_GREEN}, Y={LED_YELLOW}, R={LED_RED}, B={BUZZER_PIN}")

# Global reader instance
reader = None

def check_spi():
    """Check if SPI is enabled on the system"""
    if not os.path.exists('/dev/spidev0.0'):
        print("⚠️  Warning: SPI interface not detected (/dev/spidev0.0)")
        print("    → Run 'sudo raspi-config' and enable SPI under Interface Options")
        return False
    return True

# ========================================
# Offline Queue (SQLite)
# ========================================
QUEUE_DB = "offline_queue.db"

def init_queue_db():
    """Initialize the offline queue database"""
    conn = sqlite3.connect(QUEUE_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rfid_uid TEXT NOT NULL,
            device_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            retries INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_to_queue(rfid_uid: str):
    """Add a scan to the offline queue"""
    conn = sqlite3.connect(QUEUE_DB)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scan_queue (rfid_uid, device_id, timestamp)
        VALUES (?, ?, ?)
    ''', (rfid_uid, DEVICE_ID, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    print(f"📦 Added to offline queue: {rfid_uid}")

def get_queued_scans():
    """Get all pending scans from the queue"""
    conn = sqlite3.connect(QUEUE_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT id, rfid_uid, device_id, timestamp FROM scan_queue ORDER BY id')
    scans = cursor.fetchall()
    conn.close()
    return scans

def remove_from_queue(scan_id: int):
    """Remove a scan from the queue after successful upload"""
    conn = sqlite3.connect(QUEUE_DB)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scan_queue WHERE id = ?', (scan_id,))
    conn.commit()
    conn.close()

# ========================================
# GPIO Setup
# ========================================
def setup_gpio():
    """Initialize GPIO pins for LEDs and buzzer"""
    if not PI_MODE:
        return
    
    # Note: SimpleMFRC522 already set GPIO.BOARD mode,
    # so we do NOT call GPIO.setmode() again here.
    GPIO.setwarnings(False)
    
    # Setup LED pins as outputs
    GPIO.setup(LED_GREEN, GPIO.OUT)
    GPIO.setup(LED_YELLOW, GPIO.OUT)
    GPIO.setup(LED_RED, GPIO.OUT)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    
    # Turn all off initially
    GPIO.output(LED_GREEN, GPIO.LOW)
    GPIO.output(LED_YELLOW, GPIO.LOW)
    GPIO.output(LED_RED, GPIO.LOW)
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    
    print("✅ GPIO initialized")

def cleanup_gpio():
    """Cleanup GPIO on exit"""
    if PI_MODE:
        GPIO.cleanup()
        print("🧹 GPIO cleaned up")

def led_feedback(led_pin: int, duration: float = LED_DURATION):
    """Flash an LED for visual feedback"""
    if not PI_MODE:
        led_names = {LED_GREEN: "GREEN", LED_YELLOW: "YELLOW", LED_RED: "RED"}
        print(f"💡 LED {led_names.get(led_pin, led_pin)} ON")
        return
    
    def flash():
        GPIO.output(led_pin, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(led_pin, GPIO.LOW)
    
    # Run in background thread so it doesn't block
    threading.Thread(target=flash, daemon=True).start()

def beep(duration: float = BEEP_DURATION):
    """Short buzzer beep"""
    if not PI_MODE:
        print("🔊 BEEP")
        return
    
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(BUZZER_PIN, GPIO.LOW)

# ========================================
# API Communication
# ========================================
def send_scan(rfid_uid: str) -> dict:
    """
    Send scan to the cloud API
    Returns: response dict or None if failed
    """
    url = f"{API_URL}{SCAN_ENDPOINT}"
    payload = {
        "rfid_uid": rfid_uid,
        "device_id": DEVICE_ID
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - API unreachable")
        return None
    except requests.exceptions.Timeout:
        print("❌ Request timeout")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def process_scan(rfid_uid: str):
    """Process an RFID scan - send to API and provide feedback"""
    print(f"\n📡 Card scanned: {rfid_uid}")
    
    result = send_scan(rfid_uid)
    
    if result is None:
        # Network error - add to offline queue
        add_to_queue(rfid_uid)
        led_feedback(LED_RED)
        beep()
        time.sleep(0.2)
        beep()  # Double beep for error
        return
    
    if result.get('success'):
        action = result.get('action', 'UNKNOWN')
        student = result.get('student', {})
        name = student.get('name', 'Unknown')
        
        print(f"✅ {action}: {name}")
        
        if action == 'ENTRY':
            led_feedback(LED_GREEN)
            print(f"   🟢 Welcome, {name}!")
        else:  # EXIT
            led_feedback(LED_YELLOW)
            print(f"   🟡 Goodbye, {name}!")
        
        beep()
    else:
        # Card not recognized
        error = result.get('error', 'Unknown error')
        print(f"❌ Error: {error}")
        led_feedback(LED_RED)
        beep()
        time.sleep(0.2)
        beep()

# ========================================
# Offline Queue Processor
# ========================================
def process_offline_queue():
    """Background thread to process queued scans"""
    while True:
        time.sleep(RETRY_INTERVAL)
        
        scans = get_queued_scans()
        if not scans:
            continue
        
        print(f"\n📤 Processing {len(scans)} queued scans...")
        
        for scan_id, rfid_uid, device_id, timestamp in scans:
            result = send_scan(rfid_uid)
            
            if result and result.get('success'):
                remove_from_queue(scan_id)
                print(f"   ✅ Uploaded: {rfid_uid}")
            elif result:
                # API responded but scan failed (e.g., unknown card)
                remove_from_queue(scan_id)
                print(f"   ⚠️ Removed invalid: {rfid_uid}")
            else:
                # Still can't reach API
                print(f"   ⏳ Will retry: {rfid_uid}")
                break  # Stop trying if API is still down

# ========================================
# RFID Reader
# ========================================
def read_rfid():
    """Read RFID card and return UID as hex string"""
    global reader
    if PI_MODE:
        try:
            if reader is None:
                reader = SimpleMFRC522()
            
            print("   🔍 Place card near reader...")
            id = reader.read_id()
            if id:
                print(f"   ✨ Card detected! (Raw ID: {id})")
                # Convert to hex string (uppercase)
                return format(id, 'X')
            return None
        except Exception as e:
            print(f"   ⚠️  Hardware read error: {e}")
            # Try to reset reader on error
            reader = None
            return None
    else:
        # USB RFID reader mode - reads from stdin
        # USB RFID readers act as keyboard input: they type the UID and press Enter
        # You can also type a UID manually for testing
        uid = input("\n🔍 Scan RFID card (or type UID): ").strip().upper()
        if not uid:
            return None
        return uid

# ========================================
# Main Loop
# ========================================
def main():
    print("""
    ╔═══════════════════════════════════════════╗
    ║     📚 Library Logger - RFID Scanner      ║
    ║                                           ║
    ║     Ready to scan student cards...        ║
    ║     Press Ctrl+C to exit                  ║
    ╚═══════════════════════════════════════════╝
    """)
    
    print(f"🔧 Configuration:")
    print(f"   API URL: {API_URL}")
    print(f"   Device ID: {DEVICE_ID}")
    print(f"   Mode: {'HARDWARE (RC522)' if PI_MODE else 'USB/MANUAL INPUT'}")
    print()
    
    init_queue_db()
    if PI_MODE:
        global reader
        if check_spi():
            try:
                reader = SimpleMFRC522()
                print("   ✅ RFID Reader initialized successfully")
            except Exception as e:
                print(f"   ❌ Failed to initialize RFID Reader: {e}")
    setup_gpio()
    
    # Start offline queue processor in background
    queue_thread = threading.Thread(target=process_offline_queue, daemon=True)
    queue_thread.start()
    
    # Signal handler for clean exit
    def signal_handler(sig, frame):
        print("\n\n👋 Shutting down...")
        cleanup_gpio()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Main scanning loop
    last_scan_time = 0
    last_uid = None
    
    print("📡 Waiting for RFID card...")
    
    try:
        while True:
            try:
                uid = read_rfid()
            except EOFError:
                print("\n\n👋 Input stream closed. Shutting down...")
                cleanup_gpio()
                sys.exit(0)
            except Exception as e:
                print(f"Reader error: {e}")
                time.sleep(1)
                continue
            
            # Skip empty input
            if not uid:
                continue
            
            current_time = time.time()
            
            # Debounce - prevent duplicate reads
            if uid == last_uid and (current_time - last_scan_time) < SCAN_DELAY:
                continue
            
            last_uid = uid
            last_scan_time = current_time
            
            # Process the scan
            process_scan(uid)
            
            # Small pause to allow user to move card away
            time.sleep(0.5)
            
            print("\n📡 Waiting for next card...")
    
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        cleanup_gpio()
        sys.exit(1)

if __name__ == "__main__":
    main()
