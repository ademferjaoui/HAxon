# 🖱️ HAxon

> ⚠️ **Work in Progress:** HAxon is under active development. Currently, the application focuses exclusively on the core, essential settings that users need the most.

A lightweight, Synapse-free Windows configuration utility for Razer wired and wireless mice. **HAxon** communicates directly with your mouse or HyperPolling dongle over native USB HID—giving you instant control over DPI, polling rate, and battery status without background services, accounts, or system bloat.

## ⚙️ How It Works & Device Support

* **Direct USB HID Communication:** Rather than relying on heavy background drivers, HAxon scans connected USB HID interfaces against `mice.json` to identify your Razer device and reads/writes hardware feature reports directly to the mouse's onboard memory.

* **Adaptive UI:** Based on the detected hardware, the interface dynamically adjusts—displaying live battery telemetry for wireless devices and warning when polling rates above `1000 Hz` require a Razer HyperPolling Wireless Dongle.

* **Essential Controls Only:** To stay fast and distraction-free, HAxon intentionally focuses on the fundamentals: **DPI**, **Polling Rate**, and **Battery Level** (along with quick **Rescan** support when switching mice or dongles).

* **Broad Razer Mouse Coverage:** HAxon currently supports **Razer mice only**, covering all major wired and wireless models (including DeathAdder, Viper, Basilisk, Naga, Cobra, Orochi, and Pro/HyperSpeed variants). If a newly released model isn't recognized yet, its VID/PID can be easily added to `mice.json`.

## ✨ Key Features

* **Zero Background Bloat:** Runs only when you open it. Settings are written directly to the mouse's onboard memory via native HID feature reports.

* **Dynamic Polling Rate Control:** Automatically probes supported hardware rates—including **125 Hz**, **500 Hz**, **1000 Hz**, **2000 Hz**, **4000 Hz**, and **8000 Hz (HyperPolling)**—and adapts available options to the connected receiver.

* **DPI & Sensitivity Management:** Configure your active DPI cleanly with a slider or exact numeric input without bloated driver suites.

* **Live Battery Telemetry:** Read real-time battery percentage directly from wireless devices.
* **Minimize to Tray:** app can be minimized and shows mouse name and battery status when available  

* **100% Portable Architecture:** Leaves the Windows Registry completely untouched. Configuration files (`mouse.json` and `mice.json`) live right beside `HAxon.exe` for easy backups and updates as our goal is to reduce the footprint of synapse app.

## 🚀 Getting Started

### Portable Release

1. Go to the [**Releases**](../../releases) page and download `HAxon.zip`.

2. Extract the archive to any folder (e.g., `C:\Tools\HAxon\`).

3. Run **`HAxon.exe`**. *(Keep the `_internal` folder in the same directory as `HAxon.exe`.)*

> **Note on Windows SmartScreen:** Because HAxon is an independent, unsigned open-source binary, Windows Defender SmartScreen may display a prompt on first launch. Click **More info** → **Run anyway** to start the app.

## 📁 Configuration & Logs

On first launch, HAxon seeds editable configuration files directly into the application folder next to `HAxon.exe`:

| File | Purpose | 
| :--- | :--- | 
| `mouse.json` | Stores your saved DPI, polling rate, and active user preferences. | 
| `mice.json` | Defines supported Razer Vendor/Product IDs (VID/PID) for wired and wireless/dongle modes. | 
| `Axon.log` | Captures diagnostic details if an unexpected HID or runtime error occurs. | 

To reset HAxon to factory defaults, close the app, delete `mouse.json`, and relaunch `HAxon.exe`.

## 🛠️ Running & Building from Source

### Prerequisites

* Windows 10 / 11 (x64)

* Python 3.10 or newer

### Run Locally

```bash
git clone https://github.com/ademferjaoui/HAxon.git
cd HAxon
pip install -r requirements.txt
python app.py
```

### Build Executable with PyInstaller

```powershell
python -m PyInstaller --noconsole --onedir --name "HAxon" --icon="razer.ico" --add-data "razer.ico;." --add-data "bgIm.jpg;." --add-data "mouse.json;." --add-data "mice.json;." --exclude-module unittest --exclude-module email --exclude-module http --exclude-module xml --exclude-module pydoc --exclude-module ssl --exclude-module sqlite3 --exclude-module multiprocessing app.py
```

The compiled application will be output to `dist\HAxon\HAxon.exe`.

## ⚠️ Disclaimer

HAxon is an independent, community-built open-source project and is not affiliated with, endorsed by, or sponsored by Razer Inc. All product names and trademarks belong to their respective owners.
