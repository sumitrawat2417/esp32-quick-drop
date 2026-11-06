# ⚡ ESP32 Quick Drop

> **Ultra-Lightweight 1-File Wireless Uploader for MicroPython**  
> Drag & drop files directly onto your ESP32 root (`/`) from any web browser. Zero setup, zero dependencies, single-file drop-in.

[![MicroPython](https://img.shields.io/badge/MicroPython-v1.19+-informational.svg?logo=python&logoColor=white)](https://micropython.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero-brightgreen.svg)]()
[![Single File](https://img.shields.io/badge/Size-%3C16KB-blueviolet.svg)]()

---

## 🌟 Why Quick Drop?

Most embedded file servers require multi-file packages, web bundlers, complex installers, or heavy dependencies. 

**ESP32 Quick Drop** is built for pure simplicity and rapid prototyping:
- **1 Single File (`quick_drop.py`)**: Copy-paste into Thonny, hit **Run (F5)**, and you are done.
- **Embedded Web UI**: Self-contained glassmorphic dark-mode web application served directly from ESP32 RAM/Flash.
- **Root-Targeted Uploads**: Seamlessly upload Python scripts (`main.py`, config files, assets) straight to `/`.
- **Streamed I/O**: Chunked direct-to-flash writes with `.tmp` staging — safe from memory exhaustion on low-RAM chips.
- **No PC Tools Required After Boot**: Upload new code from your phone, tablet, or laptop over local Wi-Fi.

---

## ⚡ 60-Second Quick Start

```
   ┌──────────────┐         Wi-Fi / Hotspot         ┌──────────────┐
   │ Phone / PC   │ ══════════════════════════════> │ ESP32 Board  │
   │  Web Browser │   http://192.168.4.1 (or IP)    │ quick_drop.py│
   └──────────────┘                                 └──────────────┘
```

1. Open **[Thonny IDE](https://thonny.org/)** and connect your ESP32.
2. Open [`quick_drop.py`](quick_drop.py) in Thonny.
3. *(Optional)* Configure your home Wi-Fi credentials at the top of the file, or leave them empty for standalone Access Point mode:
   ```python
   WIFI_SSID = ""        # Leave empty for standalone AP mode
   WIFI_PASS = ""        
   ```
4. Click **Run current script (F5)** in Thonny.
5. In your Thonny shell, you will see:
   ```text
   ==================================================
     ESP32 Quick Drop is ready!
     Open in browser: http://192.168.4.1/
   ==================================================
   ```
6. Connect your phone or laptop to the Wi-Fi network **`QuickDrop-ESP32`** and navigate to **`http://192.168.4.1`** in any web browser!
7. **Drag and drop** files straight into the drop zone to flash them to the ESP32.

---

## 🥊 Quick Drop vs. File Hub — Which One Should You Use?

We also maintain **[ESP32 File Hub](https://github.com/sumitrawat2417/esp32-file-hub)**. Here is how they compare:

| Feature | ⚡ ESP32 Quick Drop (This Repo) | 🗂️ ESP32 File Hub |
| :--- | :--- | :--- |
| **Architecture** | **1 Single File** (`quick_drop.py`) | Modular package (`esp32_file_hub/`) |
| **Footprint on Flash** | **~16 KB** | ~120 KB (full UI assets & fonts) |
| **Installation** | **Zero-install** (Run directly in Thonny) | Automated installer script (`install.bat`) |
| **Directory Support** | Flat Root (`/`) only | Full recursive folder trees & breadcrumbs |
| **In-Browser Code Editor** | ❌ (Focus on speed & drop uploads) | ✅ Full Monaco/Ace style syntax editor |
| **Wi-Fi Portal** | Hardcoded or AP fallback | Dynamic Wi-Fi modal manager |
| **Best For** | **Rapid prototyping, quick testing, single-file scripts** | **Full embedded NAS, long-term project manager** |

---

## ⚙️ Configuration

All configuration is at the very top of [`quick_drop.py`](quick_drop.py):

| Variable | Default | Description |
| :--- | :--- | :--- |
| `WIFI_SSID` | `""` | Your Wi-Fi router SSID. If empty, starts standalone Hotspot mode. |
| `WIFI_PASS` | `""` | Your Wi-Fi router password. |
| `AP_SSID` | `"QuickDrop-ESP32"` | The Hotspot name broadcasted when running in AP mode. |
| `AP_PASS` | `""` | Hotspot password (leave empty for open access, or minimum 8 characters). |
| `PORT` | `80` | HTTP listening port. |

---

## 🔌 Minimal REST API

ESP32 Quick Drop exposes a straightforward HTTP API:

- `GET /` — Serves the embedded HTML5 Web Interface.
- `GET /api/list` — Returns JSON object with storage capacity (`free_mb`, `total_mb`) and file list.
- `POST /upload?file=<filename>` — Streams raw body directly to `/<filename>`.
- `GET /download?file=<filename>` — Downloads file from root with `application/octet-stream`.
- `POST /delete?file=<filename>` — Deletes file from root.
- `POST /reboot` — Safely resets the ESP32 via `machine.reset()`.

### Example (cURL Upload)
```bash
curl -X POST "http://192.168.4.1/upload?file=main.py" \
     -H "Content-Length: 1024" \
     --data-binary "@main.py"
```

---

## 💡 Pro-Tip: Auto-Run on Boot

If you want Quick Drop to start automatically whenever your ESP32 powers up:
1. Save `quick_drop.py` to your ESP32 root as **`main.py`** (or call `import quick_drop; quick_drop.start()` inside your existing `main.py`).
2. Disconnect your ESP32 from USB and power it from any USB charger or battery.
3. It will immediately broadcast `QuickDrop-ESP32`!

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

Developed with ❤️ by **[Sumit Rawat (Forbit)](https://github.com/sumitrawat2417)**.
