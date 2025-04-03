import psutil
import requests
import time
import json
from datetime import datetime
import socket
import logging

# Configuration
API_ENDPOINT = "http://your-server-address/api/scan"
API_KEY = "your-secret-api-key"
SCAN_INTERVAL = 900  # 15 minutes in seconds
LOG_FILE = "compliance_agent.log"

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_installed_software():
    """Detect running software on the system"""
    software_list = []
    for proc in psutil.process_iter(['name', 'exe', 'username']):
        try:
            software_list.append({
                'name': proc.info['name'],
                'path': proc.info['exe'],
                'user': proc.info['username']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return software_list

def send_scan_results(software_list):
    """Send scan results to the compliance server"""
    hostname = socket.gethostname()
    timestamp = datetime.utcnow().isoformat()
    
    payload = {
        'hostname': hostname,
        'software_list': software_list,
        'timestamp': timestamp
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    }
    
    try:
        response = requests.post(
            API_ENDPOINT,
            data=json.dumps(payload),
            headers=headers
        )
        response.raise_for_status()
        logging.info(f"Scan results sent successfully. Response: {response.text}")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send scan results: {str(e)}")
        return False

def main():
    logging.info("Compliance Agent started")
    while True:
        try:
            software_list = get_installed_software()
            if software_list:
                success = send_scan_results(software_list)
                if not success:
                    logging.warning("Retrying in 1 minute...")
                    time.sleep(60)  # Wait 1 minute before retry
                    continue
            else:
                logging.warning("No software detected in scan")
            
            time.sleep(SCAN_INTERVAL)
        except KeyboardInterrupt:
            logging.info("Compliance Agent stopped by user")
            break
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            time.sleep(60)  # Wait 1 minute before continuing

if __name__ == "__main__":
    main()