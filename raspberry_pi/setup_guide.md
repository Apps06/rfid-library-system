# Raspberry Pi Setup Guide for Library Logger

This guide explains how to set up the RFID scanner on your Raspberry Pi 3 B+.

## 🔧 Hardware Required

| Component | Quantity | Description |
|-----------|----------|-------------|
| Raspberry Pi 3 B+ | 1 | Main controller |
| RFID-RC522 Module | 1 | RFID reader |
| LEDs | 3 | Green, Yellow, Red |
| Resistors | 3 | 220Ω (for LEDs) |
| Buzzer (optional) | 1 | 5V active buzzer |
| Jumper Wires | ~15 | Male-to-female |
| Breadboard | 1 | For prototyping |
| RFID Cards/Tags | 2+ | For testing |

---

## 🔌 Wiring Diagram

### RFID-RC522 to Raspberry Pi

| RC522 Pin | RPi Pin | GPIO |
|-----------|---------|------|
| SDA | Pin 24 | GPIO 8 (CE0) |
| SCK | Pin 23 | GPIO 11 (SCLK) |
| MOSI | Pin 19 | GPIO 10 (MOSI) |
| MISO | Pin 21 | GPIO 9 (MISO) |
| IRQ | Not connected | - |
| GND | Pin 6 | Ground |
| RST | Pin 22 | GPIO 25 |
| 3.3V | Pin 1 | 3.3V Power |

### LED Connections

| LED Color | GPIO Pin | RPi Pin | Purpose |
|-----------|----------|---------|---------|
| 🟢 Green | GPIO 17 | Pin 11 | Entry indicator |
| 🟡 Yellow | GPIO 22 | Pin 15 | Exit indicator |
| 🔴 Red | GPIO 27 | Pin 13 | Error indicator |

**LED Wiring:**
```
GPIO Pin → 220Ω Resistor → LED Anode (+)
LED Cathode (-) → Ground
```

### Buzzer (Optional)

| Buzzer | GPIO Pin | RPi Pin |
|--------|----------|---------|
| Signal (+) | GPIO 18 | Pin 12 |
| Ground (-) | GND | Pin 14 |

---

## 📐 Visual Wiring Reference

```
Raspberry Pi GPIO Header (Top View)
┌─────────────────────────────────────┐
│ [3.3V]  1 ○ ○ 2  [5V]               │
│ [GPIO2] 3 ○ ○ 4  [5V]               │
│ [GPIO3] 5 ○ ○ 6  [GND] ← RC522 GND  │
│ [GPIO4] 7 ○ ○ 8  [GPIO14]           │
│ [GND]   9 ○ ○ 10 [GPIO15]           │
│ [GPIO17] 11 ● ○ 12 [GPIO18] ← BUZZ  │  ← GREEN LED
│ [GPIO27] 13 ● ○ 14 [GND]            │  ← RED LED
│ [GPIO22] 15 ● ○ 16 [GPIO23]         │  ← YELLOW LED
│ [3.3V]  17 ○ ○ 18 [GPIO24]          │
│ [MOSI]  19 ● ○ 20 [GND]             │  ← RC522 MOSI
│ [MISO]  21 ● ○ 22 ● [GPIO25]        │  ← RC522 MISO, RST
│ [SCLK]  23 ● ○ 24 ● [CE0]           │  ← RC522 SCK, SDA
│         ...                          │
└─────────────────────────────────────┘
● = Used pins
```

---

## 💻 Software Setup

### 1. Enable SPI Interface

```bash
sudo raspi-config
```
Navigate to: **Interface Options → SPI → Enable**

Reboot:
```bash
sudo reboot
```

### 2. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Install Python Dependencies

```bash
cd ~/library_logger/raspberry_pi
pip3 install -r requirements.txt
```

If `mfrc522` fails to install:
```bash
pip3 install spidev
pip3 install mfrc522
```

### 4. Configure API URL

Edit `config.py` and set your server URL:
```python
# For local testing (Pi and server on same network)
API_URL = "http://192.168.1.100:5000"

# For cloud deployment
API_URL = "https://your-app.onrender.com"
```

### 5. Test the Scanner

```bash
python3 rfid_scanner.py
```

---

## 🚀 Auto-Start on Boot

### Option 1: Using systemd (Recommended)

Create service file:
```bash
sudo nano /etc/systemd/system/library-scanner.service
```

Add content:
```ini
[Unit]
Description=Library RFID Scanner
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/library_logger/raspberry_pi
ExecStart=/usr/bin/python3 rfid_scanner.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable library-scanner
sudo systemctl start library-scanner
```

Check status:
```bash
sudo systemctl status library-scanner
```

### Option 2: Using rc.local

```bash
sudo nano /etc/rc.local
```

Add before `exit 0`:
```bash
cd /home/pi/library_logger/raspberry_pi && python3 rfid_scanner.py &
```

---

## 🔍 Troubleshooting

### Card Not Detected

1. Check SPI is enabled: `ls /dev/spi*` should show spidev0.0
2. Verify wiring - especially RST, SDA, and 3.3V
3. Test with: `python3 -c "from mfrc522 import SimpleMFRC522; print('OK')"`

### LED Not Working

1. Check resistor connection
2. Verify GPIO pin numbers in `config.py`
3. Test manually:
```python
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.output(17, GPIO.HIGH)  # Should light up
```

### API Connection Failed

1. Check internet: `ping google.com`
2. Verify API URL in `config.py`
3. Test API manually:
```bash
curl -X POST http://YOUR_API_URL/api/scan \
  -H "Content-Type: application/json" \
  -d '{"rfid_uid":"TEST123"}'
```

---

## 📁 File Structure on Pi

```
/home/pi/library_logger/
└── raspberry_pi/
    ├── rfid_scanner.py    # Main scanner script
    ├── config.py          # Configuration
    ├── requirements.txt   # Dependencies
    ├── offline_queue.db   # Auto-created for offline scans
    └── setup_guide.md     # This file
```

---

## ✅ Quick Test Checklist

- [ ] SPI enabled and spidev visible
- [ ] RC522 wired correctly (check 3.3V, not 5V!)
- [ ] Python dependencies installed
- [ ] API URL configured
- [ ] Test card scan works
- [ ] LEDs respond to scans
- [ ] Service enabled for auto-start
