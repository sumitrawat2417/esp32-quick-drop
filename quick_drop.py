"""
ESP32 Quick Drop — Ultra-Lightweight Wireless File Uploader for MicroPython
===========================================================================
Single-file drop-in tool to wirelessly upload files directly to your ESP32 root (/)
via a modern in-browser drag and drop interface. Zero installation, zero external dependencies.

Usage:
  1. Open this file in Thonny.
  2. Click Run (F5).
  3. Connect to Wi-Fi "QuickDrop-ESP32" and open http://192.168.4.1 in your browser!
"""

import socket
import network
import os
import gc
import time

# ================= Configuration =================
WIFI_SSID = ""        # Set your home/hotspot SSID (or leave empty for Standalone AP)
WIFI_PASS = ""        # Password for router (or empty for open network)
AP_SSID   = "QuickDrop-ESP32"
AP_PASS   = ""        # Min 8 chars, or empty for open AP
PORT      = 80

# ================= Embedded Web UI =================
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ESP32 Quick Drop</title>
<style>
:root{--bg:#0b0f19;--card:rgba(18,24,38,0.92);--border:rgba(255,255,255,0.08);--primary:#38bdf8;--accent:#818cf8;--danger:#f43f5e;--text:#f8fafc;--muted:#94a3b8}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:2rem 1rem}
.wrap{width:100%;max-width:520px;display:flex;flex-direction:column;gap:1rem}
.head{display:flex;justify-content:space-between;align-items:center;padding:0.25rem 0}
.brand{display:flex;align-items:center;gap:0.5rem;font-size:1.25rem;font-weight:700;color:#fff}
.badge{font-size:0.75rem;padding:0.2rem 0.6rem;background:rgba(56,189,248,0.1);border:1px solid rgba(56,189,248,0.25);border-radius:99px;color:var(--primary);font-family:monospace}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.25rem;box-shadow:0 8px 32px rgba(0,0,0,0.37)}
.dropzone{border:2px dashed rgba(56,189,248,0.35);border-radius:10px;padding:2.2rem 1.5rem;text-align:center;cursor:pointer;transition:all .2s;background:rgba(56,189,248,0.02)}
.dropzone:hover,.dropzone.dragover{border-color:var(--primary);background:rgba(56,189,248,0.08);transform:scale(1.01)}
.icon{font-size:2.2rem;margin-bottom:0.4rem;display:block}
.bar-box{height:6px;background:rgba(255,255,255,0.06);border-radius:99px;overflow:hidden;margin:0.75rem 0 0.25rem}
.bar-fill{height:100%;width:0;background:linear-gradient(90deg,var(--primary),var(--accent));transition:width .2s}
.status{font-size:0.8rem;color:var(--muted);text-align:center;min-height:1.2rem;margin-top:0.25rem}
.flist{list-style:none;display:flex;flex-direction:column;gap:0.4rem;max-height:260px;overflow-y:auto}
.fitem{display:flex;justify-content:space-between;align-items:center;padding:0.45rem 0.65rem;background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:6px;font-size:0.82rem}
.fname{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:280px}
.fdel{color:var(--danger);cursor:pointer;background:none;border:none;padding:0.2rem 0.4rem;font-size:0.85rem;font-weight:bold}
.fdel:hover{opacity:0.8}
.meta{display:flex;justify-content:space-between;align-items:center;font-size:0.78rem;color:var(--muted);margin-bottom:0.6rem}
.btn-sm{background:transparent;border:1px solid var(--border);color:var(--muted);padding:0.2rem 0.5rem;border-radius:4px;cursor:pointer;font-size:0.75rem}
.btn-sm:hover{color:var(--text);border-color:var(--muted)}
</style>
</head>
<body>
<div class="wrap">
  <div class="head">
    <div class="brand"><span>&#9889;</span> ESP32 Quick Drop</div>
    <span class="badge" id="ipBadge">192.168.4.1</span>
  </div>
  <div class="card">
    <div class="dropzone" id="dz" onclick="document.getElementById('fi').click()">
      <span class="icon">&#128229;</span>
      <strong style="font-size:0.95rem;">Click or Drop files here</strong>
      <p style="font-size:0.78rem;color:var(--muted);margin-top:0.25rem;">Direct upload to ESP32 root ( / )</p>
      <input type="file" id="fi" multiple style="display:none" onchange="uploadFiles(this.files)">
    </div>
    <div class="bar-box"><div class="bar-fill" id="pbar"></div></div>
    <div class="status" id="st">Ready for upload</div>
  </div>
  <div class="card">
    <div class="meta">
      <span id="storageInfo">Storage: Calculating...</span>
      <div style="display:flex;gap:0.4rem;">
        <button class="btn-sm" onclick="loadFiles()">&#128260; Refresh</button>
        <button class="btn-sm" onclick="reboot()">&#9889; Reboot</button>
      </div>
    </div>
    <ul class="flist" id="fl"></ul>
  </div>
</div>
<script>
const dz=document.getElementById('dz'),pbar=document.getElementById('pbar'),st=document.getElementById('st'),fl=document.getElementById('fl');
['dragenter','dragover'].forEach(e=>dz.addEventListener(e,ev=>{ev.preventDefault();dz.classList.add('dragover')}));
['dragleave','drop'].forEach(e=>dz.addEventListener(e,ev=>{ev.preventDefault();dz.classList.remove('dragover')}));
dz.addEventListener('drop',e=>{if(e.dataTransfer.files)uploadFiles(e.dataTransfer.files)});

async function uploadFiles(files){
  if(!files||!files.length)return;
  for(let i=0;i<files.length;i++){
    const f=files[i];
    st.textContent=`Uploading ${f.name} (${formatBytes(f.size)})...`;
    pbar.style.width='30%';
    try{
      const res=await fetch('/upload?file='+encodeURIComponent(f.name),{
        method:'POST',
        headers:{'Content-Length':f.size.toString()},
        body:f
      });
      pbar.style.width='100%';
      if(res.ok){st.textContent=`Uploaded: ${f.name}`;setTimeout(()=>pbar.style.width='0%',1000)}
      else{const t=await res.text();st.textContent=`Failed: ${t}`}
    }catch(e){st.textContent='Error uploading: '+f.name}
  }
  loadFiles();
}

async function loadFiles(){
  try{
    const r=await fetch('/api/list');
    const d=await r.json();
    document.getElementById('storageInfo').textContent=`Free: ${d.free_mb} MB / Total: ${d.total_mb} MB`;
    if(!d.files||!d.files.length){
      fl.innerHTML='<li style="color:var(--muted);text-align:center;padding:1rem;font-size:0.8rem">No files found on root ( / )</li>';
      return;
    }
    fl.innerHTML=d.files.map(f=>`
      <li class="fitem">
        <span class="fname">&#128196; ${escapeHtml(f.name)} <small style="color:var(--muted);margin-left:0.3rem">(${formatBytes(f.size)})</small></span>
        <div style="display:flex;align-items:center;gap:0.4rem;">
          <a href="/download?file=${encodeURIComponent(f.name)}" style="color:var(--primary);text-decoration:none;font-size:0.85rem;" title="Download" download>&#11015;</a>
          <button class="fdel" onclick="delFile('${escapeHtml(f.name)}')" title="Delete">&#10005;</button>
        </div>
      </li>`).join('');
  }catch(e){
    document.getElementById('storageInfo').textContent='Storage: Error';
  }
}

async function delFile(name){
  if(!confirm(`Delete "${name}"?`))return;
  await fetch('/delete?file='+encodeURIComponent(name),{method:'POST'});
  loadFiles();
}

async function reboot(){
  if(confirm('Reboot ESP32?')){fetch('/reboot',{method:'POST'});st.textContent='ESP32 is rebooting...'}
}

function formatBytes(b){if(!b||b===0)return'0 B';const k=1024,dm=1,sizes=['B','KB','MB'];const i=Math.floor(Math.log(b)/Math.log(k));return parseFloat((b/Math.pow(k,i)).toFixed(dm))+' '+sizes[i]}
function escapeHtml(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;')}
window.onload=()=>{
  document.getElementById('ipBadge').textContent=location.host||'192.168.4.1';
  loadFiles();
};
</script>
</body>
</html>
"""

# ================= Networking =================
def setup_network():
    """Establish Wi-Fi connection (STA with AP fallback)."""
    if WIFI_SSID:
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        sta.connect(WIFI_SSID, WIFI_PASS)
        print("[QuickDrop] Connecting to '{}'...".format(WIFI_SSID), end="")
        for _ in range(20):
            if sta.isconnected():
                ip = sta.ifconfig()[0]
                print("\n[QuickDrop] Connected! IP: {}".format(ip))
                return ip
            time.sleep(0.5)
            print(".", end="")
        print("\n[QuickDrop] Wi-Fi connection timed out. Falling back to AP mode.")

    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    if AP_PASS and len(AP_PASS) >= 8:
        ap.config(essid=AP_SSID, password=AP_PASS, authmode=network.AUTH_WPA_WPA2_PSK)
    else:
        ap.config(essid=AP_SSID, authmode=network.AUTH_OPEN)
    
    ip = ap.ifconfig()[0]
    print("\n[QuickDrop] Standalone Access Point active!")
    print("   SSID : {}".format(AP_SSID))
    print("   IP   : {}".format(ip))
    return ip

def get_storage():
    """Return free and total flash storage metrics in MB."""
    try:
        s = os.statvfs('/')
        free_mb = round((s[0] * s[3]) / (1024 * 1024), 2)
        total_mb = round((s[0] * s[2]) / (1024 * 1024), 2)
        return free_mb, total_mb
    except Exception:
        return 0, 0

def list_root_files():
    """List non-directory files in root /."""
    files = []
    try:
        for entry in os.ilistdir('/'):
            name = entry[0]
            is_dir = (entry[1] == 0x4000)
            if not is_dir and not name.startswith('.'):
                try:
                    size = os.stat('/' + name)[6]
                except Exception:
                    size = 0
                files.append({'name': name, 'size': size})
        files.sort(key=lambda x: x['name'].lower())
    except Exception:
        pass
    return files

# ================= HTTP Server =================
def run_server(ip):
    """Run minimal socket server with robust stream buffering."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', PORT))
    s.listen(2)

    print("\n" + "=" * 50)
    print("  ESP32 Quick Drop is ready!")
    print("  Open in browser: http://{}/".format(ip))
    print("=" * 50 + "\n")

    while True:
        cl = None
        try:
            cl, addr = s.accept()
            cl.settimeout(10.0)

            raw = b""
            while b"\r\n\r\n" not in raw and len(raw) < 4096:
                chunk = cl.recv(512)
                if not chunk:
                    break
                raw += chunk

            if not raw or b"\r\n\r\n" not in raw:
                if cl: cl.close()
                continue

            header_bytes, initial_body = raw.split(b"\r\n\r\n", 1)
            lines = header_bytes.decode('utf-8', 'ignore').split("\r\n")
            if not lines:
                if cl: cl.close()
                continue

            req_line = lines[0].strip()
            parts = req_line.split()
            if len(parts) < 2:
                if cl: cl.close()
                continue

            method, full_path = parts[0], parts[1]
            path = full_path.split('?')[0]
            query = {}
            if '?' in full_path:
                for q in full_path.split('?')[1].split('&'):
                    if '=' in q:
                        k, v = q.split('=', 1)
                        v = v.replace('+', ' ').replace('%20', ' ')
                        query[k] = v

            headers = {}
            for hline in lines[1:]:
                if ':' in hline:
                    k, v = hline.split(':', 1)
                    headers[k.strip().lower()] = v.strip()

            # Routing
            if method == 'GET' and (path == '/' or path == '/index.html'):
                cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nConnection: close\r\n\r\n")
                cl.sendall(HTML.encode('utf-8'))

            elif method == 'GET' and path == '/api/list':
                free_mb, total_mb = get_storage()
                files = list_root_files()
                import json
                resp = json.dumps({'free_mb': free_mb, 'total_mb': total_mb, 'files': files})
                cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n")
                cl.sendall(resp.encode('utf-8'))

            elif method == 'POST' and path == '/upload':
                filename = query.get('file', 'uploaded.bin').strip('/')
                clength = int(headers.get('content-length', 0))

                if not filename or clength <= 0:
                    cl.send(b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\nInvalid parameters")
                else:
                    target_path = '/' + filename
                    tmp_path = target_path + '.tmp'
                    print("[QuickDrop] Receiving '{}' ({} bytes)...".format(filename, clength))

                    with open(tmp_path, 'wb') as f:
                        if initial_body:
                            f.write(initial_body)
                        received = len(initial_body)
                        while received < clength:
                            chunk = cl.recv(min(1024, clength - received))
                            if not chunk:
                                break
                            f.write(chunk)
                            received += len(chunk)

                    if received == clength:
                        try:
                            os.remove(target_path)
                        except Exception:
                            pass
                        os.rename(tmp_path, target_path)
                        print("[QuickDrop] [OK] Saved to '{}'".format(target_path))
                        cl.send(b"HTTP/1.1 200 OK\r\nConnection: close\r\n\r\nOK")
                    else:
                        try:
                            os.remove(tmp_path)
                        except Exception:
                            pass
                        cl.send(b"HTTP/1.1 500 Error\r\nConnection: close\r\n\r\nIncomplete upload")

            elif method == 'GET' and path == '/download':
                filename = query.get('file', '').strip('/')
                target_path = '/' + filename
                try:
                    size = os.stat(target_path)[6]
                    header = "HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Disposition: attachment; filename=\"{}\"\r\nContent-Length: {}\r\nConnection: close\r\n\r\n".format(filename, size)
                    cl.send(header.encode('utf-8'))
                    with open(target_path, 'rb') as f:
                        while True:
                            chunk = f.read(1024)
                            if not chunk:
                                break
                            cl.sendall(chunk)
                except Exception:
                    cl.send(b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\nFile not found")

            elif method == 'POST' and path == '/delete':
                filename = query.get('file', '').strip('/')
                target_path = '/' + filename
                try:
                    os.remove(target_path)
                    cl.send(b"HTTP/1.1 200 OK\r\nConnection: close\r\n\r\nDeleted")
                except Exception:
                    cl.send(b"HTTP/1.1 500 Error\r\nConnection: close\r\n\r\nDelete failed")

            elif method == 'POST' and path == '/reboot':
                cl.send(b"HTTP/1.1 200 OK\r\nConnection: close\r\n\r\nRebooting")
                cl.close()
                time.sleep(1)
                import machine
                machine.reset()

            else:
                cl.send(b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\nNot Found")

            if cl: cl.close()
            gc.collect()

        except Exception as e:
            try:
                if cl: cl.close()
            except Exception:
                pass
            gc.collect()

def start():
    """Main application entry point."""
    ip = setup_network()
    run_server(ip)

if __name__ == '__main__':
    start()
