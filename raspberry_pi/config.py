# ========================================
# Raspberry Pi RFID Scanner Configuration
# ========================================

# Cloud API Configuration
# Replace with your actual server URL when deployed
API_URL = "http://192.168.1.12:5000"  # Local testing (using 192.168.1.12)
# API_URL = "https://your-app.onrender.com"  # Production (e.g., Render)
# API_URL = "https://your-app.railway.app"   # Production (e.g., Railway)

# RFID Scan Endpoint
SCAN_ENDPOINT = "/api/scan"

# Device ID (unique identifier for this scanner)
DEVICE_ID = "GATE_01"

# ========================================
# GPIO Pin Configuration (BCM numbering)
# ========================================

# LED Pins
LED_GREEN = 17   # Success - Entry
LED_RED = 27     # Error / Unknown card
LED_YELLOW = 22  # Exit

# Buzzer Pin (optional)
BUZZER_PIN = 18

# ========================================
# Timing Configuration
# ========================================

# Delay between scans (seconds) - prevents duplicate reads
SCAN_DELAY = 3.0

# LED on duration (seconds)
LED_DURATION = 1.0

# Buzzer beep duration (seconds)
BEEP_DURATION = 0.1

# Offline queue retry interval (seconds)
RETRY_INTERVAL = 30
