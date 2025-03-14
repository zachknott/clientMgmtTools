import socket
import os
import platform
import subprocess
import requests
import time

def get_ip_addresses():
    """Collect all IPv4 addresses from network interfaces."""
    try:
        output = subprocess.check_output(["ip", "addr", "show"], text=True)
        ip_addresses = []
        for line in output.splitlines():
            if "inet " in line and "inet6" not in line:  # IPv4 only
                parts = line.split()
                ip = parts[1].split("/")[0]
                ip_addresses.append(ip)
        return ip_addresses
    except Exception as e:
        print(f"Error getting IP addresses on Linux: {e}")
        return []
    

if __name__ == "__main__":
    # Define the server URL
    SERVER_URL = "http://192.168.2.7:8000"
    PACKET_COUNT = 100

    # Collect system information
    hostname = socket.gethostname()
    
    try:
        username = os.getlogin()
    except:
        username = os.environ.get("USER", "unknown")

    try:
        try:
            operating_system = os.uname()
        except:
            operating_system = platform.system()
    except Exception as e:
        operating_system = f"Unable to retrieve OS Info: {e}"

    ip_addresses = get_ip_addresses()
    
    # Package system info into a dictionary
    info = {
        "hostname": hostname,
        "username": username,
        "ip_addresses": ip_addresses,
        "operating_system": operating_system
    }

    # Upload system info as JSON to the server
    try:
        response = requests.post(f"{SERVER_URL}/{hostname}_system_info", json=info)
        if response.status_code == 200:
            print("System info uploaded successfully.")
        else:
            print(f"Failed to upload system info: {response.status_code}")
    except Exception as e:
        print(f"Error uploading system info: {e}")
        
# curl http://192.168.2.7:8000/test.txt -o test.txt
# curl -X POST --data-binary @read1.pcap http://192.168.2.7:8000/read1.pcap


    # Capture network traffic using tcpdump
    timestamp = time.strftime("%Y-%m-%d_%H:%M:%S")
    filename = f"{hostname}_{timestamp}.pcap"
     
    cmd = ["tcpdump", "-c", str(PACKET_COUNT), "-w", filename]
    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode == 0:
            print("tcpdump capture completed.")
            # Upload the capture file to the server
            try:
                with open(filename, "rb") as f:
                    response = requests.post(f"{SERVER_URL}/{filename}", data=f)
                if response.status_code == 200:
                    print("Capture file uploaded successfully.")
                else:
                    print(f"Failed to upload capture file: {response.status_code}")
            except Exception as e:
                print(f"Error uploading capture file: {e}")
        else:
            print(f"tcpdump failed with return code {process.returncode}")
            print(process.stderr)
    except Exception as e:
        print(f"Error running tcpdump: {e}")